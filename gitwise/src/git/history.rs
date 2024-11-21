use anyhow::Result;
use git2::{Repository, Commit};

pub fn get_branch_commits<'a>(repo: &'a Repository, branch_name: &str) -> Result<Vec<Commit<'a>>> {
    let branch = repo.find_branch(branch_name, git2::BranchType::Local)?;
    let mut revwalk = repo.revwalk()?;
    
    revwalk.push(branch.get().target().unwrap())?;
    
    let commits = revwalk
        .map(|oid| repo.find_commit(oid.unwrap()))
        .collect::<Result<Vec<_>, _>>()?;
    
    Ok(commits)
}
