use anyhow::{Result, Context};
use async_openai::{
    types::{
        ChatCompletionRequestSystemMessage,
        ChatCompletionRequestUserMessage,
        ChatCompletionRequestUserMessageContent,
        CreateChatCompletionRequest,
        Role,
    },
    Client, config::OpenAIConfig,
};
use git2::Diff;
use std::env;

pub struct AiEngine {
    client: Client<OpenAIConfig>,
}

impl AiEngine {
    /// Create a new AI engine
    pub fn new() -> Result<Self> {
        dotenv::dotenv().ok();
        let api_key = env::var("OPENAI_API_KEY")
            .context("OPENAI_API_KEY environment variable not found")?;
        
        let client = Client::with_config(OpenAIConfig::new().with_api_key(api_key));
        Ok(Self { client })
    }

    /// Summarize a git diff using AI
    pub async fn summarize_diff(&self, diff: &Diff<'_>, custom_prompt: Option<&str>) -> Result<String> {
        let mut diff_text = String::new();
        diff.print(git2::DiffFormat::Patch, |_delta, _hunk, line| {
            use git2::DiffLineType::*;
            match line.origin_value() {
                Addition => diff_text.push_str(&format!("+{}", String::from_utf8_lossy(line.content()))),
                Deletion => diff_text.push_str(&format!("-{}", String::from_utf8_lossy(line.content()))),
                Context => diff_text.push_str(&format!(" {}", String::from_utf8_lossy(line.content()))),
                _ => (),
            }
            true
        })?;

        let base_prompt = "You are a helpful AI that summarizes git diffs. Focus on the key changes and their implications. Be concise but informative.";
        let prompt = if let Some(custom) = custom_prompt {
            format!("{}. Additional instruction: {}", base_prompt, custom)
        } else {
            base_prompt.to_string()
        };

        let messages = vec![
            ChatCompletionRequestSystemMessage {
                content: Some(prompt),
                name: None,
                role: Role::System,
            }.into(),
            ChatCompletionRequestUserMessage {
                content: Some(ChatCompletionRequestUserMessageContent::Text(
                    format!("Please summarize this git diff:\n```\n{}\n```", diff_text)
                )),
                name: None,
                role: Role::User,
            }.into(),
        ];

        let request = CreateChatCompletionRequest {
            model: "gpt-3.5-turbo".into(),
            messages,
            temperature: Some(0.7),
            max_tokens: Some(512),
            ..Default::default()
        };

        let response = self.client.chat().create(request).await?;
        let summary = response.choices[0]
            .message
            .content
            .clone()
            .unwrap_or_else(|| "No summary available.".to_string());

        Ok(summary)
    }

    /// Generate a commit message for the given diff
    pub async fn generate_commit_message(&self, diff: &Diff<'_>) -> Result<String> {
        let mut changes = String::new();
        diff.print(git2::DiffFormat::Patch, |delta, _hunk, line| {
            if let Some(path) = delta.new_file().path() {
            match line.origin_value() {
                    git2::DiffLineType::Addition => changes.push_str(&format!("+ {} ({})\n", String::from_utf8_lossy(line.content()), path.display())),
                    git2::DiffLineType::Deletion => changes.push_str(&format!("- {} ({})\n", String::from_utf8_lossy(line.content()), path.display())),
                _ => (),
                }
            }
            true
        })?;

        if changes.is_empty() {
            return Ok("No changes detected.".to_string());
        }

        let messages = vec![
            ChatCompletionRequestSystemMessage {
                content: Some("You are a helpful AI that generates git commit messages. Follow these rules strictly:\n\
                         1. Format must be:\n\
                            - First line: Short summary in imperative mood, max 50 chars\n\
                            - Blank line\n\
                            - Detailed description wrapped at 72 chars\n\
                         2. First line must:\n\
                            - Use imperative mood ('Add' not 'Added')\n\
                            - Not end with a period\n\
                            - Be max 50 characters\n\
                            - Accurately describe the main change in the diff\n\
                         3. Description must:\n\
                            - Start with a blank line after the summary\n\
                            - Explain WHY the changes in the diff were made\n\
                            - Wrap text at 72 characters\n\
                            - Use proper punctuation\n\
                            - Be specific to the actual changes shown\n\
                            - Include affected files or components\n\
                         4. Example:\n\
                            Add user authentication to API endpoints\n\
                            \n\
                            Implements JWT-based authentication to secure all API endpoints in\n\
                            auth.rs. This change is required for GDPR compliance and improves\n\
                            our overall security posture by preventing unauthorized access.\n\
                            \n\
                            Modified files:\n\
                            - auth.rs: Added JWT verification\n\
                            - main.rs: Integrated auth middleware\n\
                         5. Important:\n\
                            - Focus ONLY on the changes shown in the diff\n\
                            - Do not make up changes that aren't in the diff\n\
                            - Be specific about what files or components changed".to_string()),
                name: None,
                role: Role::System,
            }.into(),
            ChatCompletionRequestUserMessage {
                content: Some(ChatCompletionRequestUserMessageContent::Text(
                    format!("Analyze these changes and create a commit summary:\n```\n{}\n```", changes)
                )),
                name: None,
                role: Role::User,
            }.into(),
        ];

        let request = CreateChatCompletionRequest {
            model: "gpt-3.5-turbo".into(),
            messages,
            temperature: Some(0.3),
            max_tokens: Some(300),
            ..Default::default()
        };

        let response = self.client.chat().create(request).await?;
        let message = response.choices[0]
            .message
            .content
            .clone()
            .unwrap_or_else(|| "Failed to generate commit message.".to_string());

        Ok(message)
    }

    /// Analyze changes and group them by feature
    pub async fn analyze_changes(&self, staged_diff: &Diff<'_>, unstaged_diff: &Diff<'_>, prompt: Option<&str>) -> Result<Vec<Vec<String>>> {
        let mut all_changes = String::new();
        
        // Helper function to format diff
        let mut format_diff = |diff: &Diff<'_>, prefix: &str| -> Result<()> {
            diff.print(git2::DiffFormat::Patch, |delta, _hunk, line| {
                if let Some(path) = delta.new_file().path() {
                    match line.origin_value() {
                        git2::DiffLineType::Addition => all_changes.push_str(&format!("{} +{} ({})\n", prefix, String::from_utf8_lossy(line.content()), path.display())),
                        git2::DiffLineType::Deletion => all_changes.push_str(&format!("{} -{} ({})\n", prefix, String::from_utf8_lossy(line.content()), path.display())),
                        _ => (),
                    }
                }
                true
            })?;
            Ok(())
        };
        
        // Format both staged and unstaged changes
        format_diff(staged_diff, "[Staged]")?;
        format_diff(unstaged_diff, "[Unstaged]")?;
        
        if all_changes.is_empty() {
            return Ok(vec![]); // Return empty array if no changes
        }
        
        let default_prompt = "You are an expert Git user who thinks holistically about changes. \
            FIRST AND MOST IMPORTANT RULE: If all the changes could reasonably be part of one development effort, \
            return them as a single group. Default to this approach unless there are COMPLETELY unrelated changes. \
            \
            When deciding whether to group ALL changes together, consider: \
            - Are they part of the same general development session? \
            - Could they be described under one high-level goal? \
            - Do they affect related areas of the codebase? \
            - Would they make sense to review together? \
            If YES to ANY of these, PUT EVERYTHING IN ONE GROUP. \
            \
            Only split into multiple groups if you find changes that are: \
            1. Completely different features with zero relationship \
            2. Fixes for entirely separate bugs \
            3. Changes that absolutely cannot be described in one commit message \
            \
            Examples of changes that should be ONE group: \
            - A feature implementation + its tests + docs + config changes \
            - Multiple refactorings across the codebase \
            - A mix of bug fixes in related components \
            - Frontend changes + related backend updates \
            - Multiple improvements to similar functionality \
            \
            Remember: \
            - STRONGLY PREFER one large group over multiple small ones \
            - If unsure, put everything in one group \
            - It's better to group too much than too little \
            - Only split if it would be IMPOSSIBLE to describe the changes together \
            \
            IMPORTANT: Your response must be a valid JSON array where each element is an array of file paths. \
            Example response format: [[\"file1.rs\", \"file2.rs\", \"test1.rs\", \"mod.rs\", \"config.toml\", \"docs.md\"]] \
            Note how the example shows everything in ONE group - this is what we usually want! \
            Only output the JSON array, no other text or explanations.";

        let messages = vec![
            ChatCompletionRequestSystemMessage {
                content: Some(default_prompt.to_string()),
                name: None,
                role: Role::System,
            }.into(),
            ChatCompletionRequestUserMessage {
                content: Some(ChatCompletionRequestUserMessageContent::Text(
                    format!("Group these changes by feature (custom focus: {}):\n```\n{}\n```",
                        prompt.unwrap_or("none"),
                        all_changes)
                )),
                name: None,
                role: Role::User,
            }.into(),
        ];

        let request = CreateChatCompletionRequest {
            model: "gpt-3.5-turbo".into(),
            messages,
            temperature: Some(0.3),
            max_tokens: Some(1000),
            ..Default::default()
        };

        let response = self.client.chat().create(request).await?;
        let message = response.choices[0]
            .message
            .content
            .clone()
            .unwrap_or_else(|| "[]".to_string());

        // Try to parse the response
        let groups: Vec<Vec<String>> = serde_json::from_str(&message)
            .with_context(|| format!("Failed to parse AI response as JSON array of file groups. Response was: {}", message))?;

        Ok(groups)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use git2::Repository;
    use tempfile::TempDir;

    #[tokio::test]
    async fn test_diff_summary() {
        let engine = AiEngine::new().unwrap();
        let temp_dir = TempDir::new().unwrap();
        let repo = Repository::init(temp_dir.path()).unwrap();
        
        // Create an empty diff
        let diff = repo.diff_tree_to_tree(None, None, None).unwrap();
        let summary = engine.summarize_diff(&diff, None).await.unwrap();
        assert!(summary.contains("No summary available."));
    }
}
