"""Sphinx configuration file."""

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

project = "Swarmer"
copyright = "2024, Jorik Schellekens"
author = "Jorik Schellekens"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
