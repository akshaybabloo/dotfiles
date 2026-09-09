# Dotfiles

[![Static Badge](https://img.shields.io/badge/dotfiles-docs-blue)](https://dotfiles.gollahalli.com)

Some helpful dotfiles for your system.

## Installation

```bash
git clone https://github.com/akshaybabloo/dotfiles.git
cd dotfiles
./bootstrap.sh
```

This should list out any dependencies that are missing. You can manually install them if you want to.

## Files Used

- `functions.sh`: Contains all the custom functions used in the dotfiles.
- `aliases.sh`: Contains all the custom aliases used in the dotfiles.
- `bootstrap.sh`: Script to set up the dotfiles environment.
- `main.sh`: The main entry point for the dotfiles, sourced by the shell rc file.
- `extract_docs.sh`: Script to extract documentation from the dotfiles scripts, it's not used directly by the user.
- `justfile`: Contains the task definitions for building docs and other project-related tasks.
