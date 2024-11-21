use anyhow::Result;
use git2::{Repository, Diff};

pub fn get_staged_changes<'a>(repo: &'a Repository) -> Result<Diff<'a>> {
    let head_tree = repo.head()?.peel_to_tree()?;
    
    let diff = repo.diff_tree_to_index(
        Some(&head_tree),
        None,
        None,
    )?;
    
    Ok(diff)
}
