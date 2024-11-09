{ pkgs ? import <nixpkgs> {} }:

let
  poetry2nix = import (pkgs.fetchFromGitHub {
    owner = "nix-community";
    repo = "poetry2nix";
    rev = "1.5.3";  # Pin to a specific version
    sha256 = "...";  # Add proper hash
  }) {
    inherit pkgs;
    inherit (pkgs) python3;
  };

  telegram-bot = poetry2nix.mkPoetryApplication {
    projectDir = ./telegram-bot;
    preferWheels = true;
  };

  serviceConfig = {
    description = "Telegram Bot Service";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      Type = "simple";
      User = "telegram-bot";
      ExecStart = "${telegram-bot}/bin/telegram-bot";
      Restart = "always";
      RestartSec = "3";
      Environment = [
        "TELEGRAM_BOT_TOKEN=%I"
        "POLLING_INTERVAL=3.0"
        "LOG_LEVEL=INFO"
      ];
    };
  };
in {
  inherit telegram-bot;
  inherit serviceConfig;
} 