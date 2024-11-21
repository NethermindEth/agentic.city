# GitWise 🌳

An intelligent Git history exploration and manipulation tool powered by AI.

## Current Features

### 🔍 AI-Powered Diff Summarization
- Get intelligent summaries of git differences
- Support for any git reference (branches, commits, tags)
- Understand complex changes at a glance
- Compare staged changes or between any two references

### 🤖 Smart Commit Messages
- Generate descriptive commit messages automatically
- Follows git commit message best practices
- AI-powered understanding of code changes
- Imperative mood and concise descriptions

### 📜 Advanced Git History
- Explore commit history with AI summaries
- Start from any git reference (branch, tag, or commit)
- Flexible reference syntax support
- Semantic understanding of code evolution

### 🎯 Git Reference Support
- Flexible reference resolution for all commands
- Supports:
  * Branch names (e.g., `main`, `feature/new-feature`)
  * Full commit hashes
  * Short commit hashes (minimum 4 characters)
  * Tags
  * Relative references (e.g., `HEAD~1`, `HEAD^`)

## Planned Features

### 🔎 Smart Branch Comparison (Coming Soon)
- Compare any two branches with AI-powered summaries
- Get high-level insights about changes between branches
- Understand complex changes at a glance

### 🚀 Intelligent PR Management (Coming Soon)
- Generate comprehensive PR descriptions automatically
- Seamless integration with GitHub CLI
- One-command PR creation and publishing

### 📦 Smart Staging (Coming Soon)
- Automatically group staged changes by logical units
- Generate meaningful commit messages for each group
- Improve commit granularity without manual file selection

### 🔍 Semantic Git History Search (Coming Soon)
- Search through commit history using natural language
- Find related commits using semantic similarity
- Vector embedding powered search for better results

### ✨ History Rewriting (Coming Soon)
- Improve commit message quality across entire branches
- Safe defaults with new branch creation
- Integrity checks to ensure content preservation
- Interactive mode for fine-grained control

## Installation

### Prerequisites
- Rust (1.70 or later)
- Git
- OpenAI API key
- GitHub CLI (for upcoming PR-related features)

### Building from Source
```bash
# Clone the repository
git clone https://github.com/yourusername/gitwise.git
cd gitwise

# Create .env file and add your OpenAI API key
echo "OPENAI_API_KEY=your-api-key-here" > .env

# Build the project
cargo build --release

# The binary will be available at
./target/release/gitwise
```

### Current Usage

```bash
# Get help
gitwise --help

# Summarize changes between branches
gitwise diff main feature/new-feature

# Summarize staged changes
gitwise diff --staged

# Compare specific commits
gitwise diff abc123 def456

# Compare with relative references
gitwise diff HEAD~3 HEAD

# Customize diff summary behavior
gitwise diff main feature/new-feature --prompt "Focus on security-related changes"
gitwise diff HEAD~3 HEAD --prompt "List only modified function names"
gitwise diff --staged --prompt "Summarize in bullet points"

# Generate commit message for staged changes
gitwise commit

# View history with AI summaries
gitwise history --count 5

# View history from a specific reference
gitwise history --reference feature/my-branch

# Customize history summary behavior
gitwise history --count 3 --prompt "Focus on API changes"
gitwise history --reference main --prompt "Group changes by component"
```

### AI Customization

The `--prompt` option allows you to customize how the AI summarizes changes. Here are some examples:

#### For Diffs
- `--prompt "Focus on security changes"`
- `--prompt "List only modified function names"`
- `--prompt "Highlight performance impacts"`
- `--prompt "Summarize in bullet points"`
- `--prompt "Group by component or module"`

#### For History
- `--prompt "Focus on API changes"`
- `--prompt "Show only breaking changes"`
- `--prompt "Organize by feature area"`
- `--prompt "Include test coverage changes"`
- `--prompt "List affected dependencies"`

### Coming Soon
```bash
# Generate PR description
gitwise pr describe

# Create PR and publish
gitwise pr publish

# Smart staging of changes
gitwise stage

# Search through git history
gitwise search "database optimization changes"

# Rewrite branch history
gitwise rewrite feature/my-branch
```

## Development

### Project Structure
```
src/
  ├── main.rs           # Entry point and CLI handling
  ├── ai/               # AI integration for summaries
  ├── cli/              # CLI interface (coming soon)
  ├── ui/               # TUI components (coming soon)
  ├── git/              # Git operations (coming soon)
  └── utils/            # Common utilities
```

### Contributing
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments
- Built with [Rust](https://www.rust-lang.org/)
- Git operations via [git2-rs](https://github.com/rust-lang/git2-rs)
- AI powered by [OpenAI](https://openai.com/)
- Terminal UI powered by [Ratatui](https://github.com/tui-rs-revival/ratatui) (coming soon)
