{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    poetry
    python312  # Matches your pyproject.toml
  ];

  shellHook = ''
    # Setup Poetry environment
    export POETRY_VIRTUALENVS_IN_PROJECT=1
  '';
} 