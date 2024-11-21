use anyhow::Result;
use git2::{Repository, Diff};
use std::path::Path;

mod diff;
mod history;
mod staging;

pub struct GitRepo {
    repo: Repository,
}

impl GitRepo {
    /// Open a git repository at the given path
    pub fn open<P: AsRef<Path>>(path: P) -> Result<Self> {
        let repo = Repository::open(path)?;
        Ok(Self { repo })
    }

    /// Open the git repository in the current directory
    pub fn open_current() -> Result<Self> {
        let repo = Repository::open_from_env()?;
        Ok(Self { repo })
    }

    /// Get the diff between two branches
    pub fn diff_branches<'a>(&'a self, source: &str, target: &str) -> Result<Diff<'a>> {
        diff::get_branch_diff(&self.repo, source, target)
    }

    /// Get all staged changes
    pub fn get_staged_changes<'a>(&'a self) -> Result<Diff<'a>> {
        staging::get_staged_changes(&self.repo)
    }

    /// Get all commits in a branch
    pub fn get_branch_commits<'a>(&'a self, branch_name: &str) -> Result<Vec<git2::Commit<'a>>> {
        history::get_branch_commits(&self.repo, branch_name)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_open_repo() {
        let temp_dir = TempDir::new().unwrap();
        Repository::init(temp_dir.path()).unwrap();
        
        let repo = GitRepo::open(temp_dir.path());
        assert!(repo.is_ok());
    }
}
