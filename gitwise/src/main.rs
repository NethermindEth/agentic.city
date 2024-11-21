use anyhow::Result;
use clap::{Parser, Subcommand};
use git2::{Repository, Oid};

mod ai;
mod utils;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Summarize changes between git references
    Diff {
        /// First git reference (branch, commit, or tag)
        #[arg(default_value = "HEAD")]
        from: String,
        /// Second git reference (branch, commit, or tag)
        #[arg()]
        to: Option<String>,
        /// Show staged changes instead
        #[arg(short, long)]
        staged: bool,
    },
    /// Generate a commit message for staged changes
    Commit,
    /// Summarize git history
    History {
        /// Git reference to start from (branch, commit, or tag)
        #[arg(default_value = "HEAD")]
        reference: String,
        /// Number of commits to summarize
        #[arg(short, long, default_value_t = 5)]
        count: u32,
    },
}

/// Resolve a git reference (branch, tag, or commit hash) to a commit
fn resolve_reference(repo: &Repository, reference: &str) -> Result<Oid> {
    // Try as a direct reference first (branch or tag)
    if let Ok(reference) = repo.find_reference(reference) {
        return Ok(reference.peel_to_commit()?.id());
    }

    // Try as a revision (commit hash, HEAD~1, etc)
    if let Ok(revspec) = repo.revparse_single(reference) {
        return Ok(revspec.peel_to_commit()?.id());
    }

    // Try as a short commit hash
    let partial_hash = reference.to_string();
    if partial_hash.len() >= 4 {
        let mut found_oid = None;
        repo.odb()?.foreach(|oid| {
            if oid.to_string().starts_with(&partial_hash) {
                found_oid = Some(*oid);
                false // Stop iteration
            } else {
                true // Continue iteration
            }
        })?;
        
        if let Some(oid) = found_oid {
            return Ok(oid);
        }
    }

    Err(anyhow::anyhow!("Could not resolve git reference: {}", reference))
}

#[tokio::main]
async fn main() -> Result<()> {
    dotenv::dotenv().ok();
    let cli = Cli::parse();
    let engine = ai::AiEngine::new()?;

    match cli.command {
        Commands::Diff { from, to, staged } => {
            let repo = Repository::open_from_env()?;
            let diff = if staged {
                // Get diff of staged changes
                let mut opts = git2::DiffOptions::new();
                let head_tree = repo.head()?.peel_to_tree()?;
                repo.diff_tree_to_index(Some(&head_tree), None, Some(&mut opts))?
            } else {
                // Get diff between references
                let from_commit = repo.find_commit(resolve_reference(&repo, &from)?)?;
                let from_tree = from_commit.tree()?;

                let to_tree = if let Some(to) = to {
                    let to_commit = repo.find_commit(resolve_reference(&repo, &to)?)?;
                    to_commit.tree()?
                } else {
                    // If no 'to' reference is provided, use the working directory
                    repo.head()?.peel_to_tree()?
                };

                repo.diff_tree_to_tree(Some(&from_tree), Some(&to_tree), None)?
            };

            let summary = engine.summarize_diff(&diff).await?;
            println!("Changes Summary:\n{}", summary);
        }
        Commands::Commit => {
            let repo = Repository::open_from_env()?;
            
            // Check if there are staged changes
            let mut index = repo.index()?;
            if index.is_empty() {
                println!("No changes to commit");
                return Ok(());
            }
            
            // Get the diff of staged changes
            let mut opts = git2::DiffOptions::new();
            let head_tree = repo.head()?.peel_to_tree()?;
            let diff = repo.diff_tree_to_index(Some(&head_tree), None, Some(&mut opts))?;
            
            let message = engine.generate_commit_message(&diff).await?;
            
            // Create the commit
            let signature = repo.signature()?;
            let tree_id = index.write_tree()?;
            let tree = repo.find_tree(tree_id)?;
            let parent = repo.head()?.peel_to_commit()?;
            
            repo.commit(
                Some("HEAD"),
                &signature,
                &signature,
                &message,
                &tree,
                &[&parent],
            )?;
            
            println!("Created commit with message:\n{}", message);
        }
        Commands::History { reference, count } => {
            let repo = Repository::open_from_env()?;
            let start_commit = repo.find_commit(resolve_reference(&repo, &reference)?)?;
            
            let mut revwalk = repo.revwalk()?;
            revwalk.push(start_commit.id())?;
            revwalk.set_sorting(git2::Sort::TIME)?;

            let mut summaries = Vec::new();
            for (i, oid) in revwalk.take(count as usize).enumerate() {
                let oid = oid?;
                let commit = repo.find_commit(oid)?;
                let tree = commit.tree()?;
                
                let parent = commit.parent(0).ok();
                let parent_tree = parent.as_ref().map(|c| c.tree().ok()).flatten();
                
                let diff = repo.diff_tree_to_tree(parent_tree.as_ref(), Some(&tree), None)?;
                let summary = engine.summarize_diff(&diff).await?;
                
                summaries.push(format!(
                    "Commit {} ({}):\n{}\n",
                    &oid.to_string()[..7],
                    commit.summary().unwrap_or("No summary"),
                    summary
                ));

                if i < count as usize - 1 {
                    summaries.push(String::from("\n---\n\n"));
                }
            }

            println!("Git History Summary:\n");
            for summary in summaries {
                println!("{}", summary);
            }
        }
    }

    Ok(())
}
