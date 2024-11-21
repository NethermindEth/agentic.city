use anyhow::Result;
use git2::Repository;

/// Open the git repository in the current directory
pub fn get_current_repo() -> Result<Repository> {
    Ok(Repository::open_from_env()?)
}
