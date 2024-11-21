use anyhow::Result;
use git2::{Repository, Diff};
use std::path::Path;

mod diff;
mod history;
pub mod staging;

// Re-export commonly used items
pub use diff::*;
pub use history::*;
pub use staging::*;
