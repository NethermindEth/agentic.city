{
  description = "AgenticCity";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        p2nix = poetry2nix.lib.mkPoetry2Nix { inherit pkgs; };
        
        telegram-bot = p2nix.mkPoetryApplication {
          projectDir = ./telegram-bot;
          preferWheels = true;
          pyproject = ./telegram-bot/pyproject.toml;
          overrides = p2nix.defaultPoetryOverrides;
        };

        test-script = pkgs.writeScriptBin "run-tests" ''
          #!${pkgs.stdenv.shell}
          cd telegram-bot && ${p2nix.mkPoetryEnv { 
            projectDir = ./telegram-bot;
            preferWheels = true;
            groups = [ "dev" "main" ];
            overrides = p2nix.defaultPoetryOverrides.extend (self: super: {
              python-telegram-bot = super.python-telegram-bot.overridePythonAttrs (old: {
                buildInputs = (old.buildInputs or [ ]) ++ [ super.hatchling ];
              });
            });
          }}/bin/pytest tests/ -v
        '';

        serviceConfig = {
          description = "AgenticCity";
          after = [ "network.target" ];
          wantedBy = [ "multi-user.target" ];
          serviceConfig = {
            Type = "simple";
            User = "telegram-bot";
            ExecStart = "${telegram-bot}/bin/telegram-bot";
            Restart = "always";
            RestartSec = "3";
            EnvironmentFile = "/etc/telegram-bot/.env";
          };
        };

      in rec {
        packages = {
          inherit telegram-bot serviceConfig;
          default = telegram-bot;
        };

        apps.test = flake-utils.lib.mkApp {
          drv = test-script;
        };

        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            poetry
            python312
          ];
          shellHook = ''
            export POETRY_VIRTUALENVS_IN_PROJECT=1
          '';
        };
      });
} 