---
layout: doc
title: Get Started
description: Get started with dotfiles.
next: 
    text: 'Functions'
    link: '/functions'
---

# Using Dotfiles

::: danger Note
Do not run the install script with `sudo`. Aliases and functions can be used with `sudo` if you want to.
:::

Some helpful dotfiles for your system.

## Requirements

- Shell: `bash` or `zsh`
- Package manager: `apt`, `dnf`, `yum`, `pacman`, or Homebrew (`brew`)
- Internet access (the script will install basic tools if needed)

The installer ensures `curl` and `git` are present by using your package manager.

## Installation

Clone the repository:

```sh
git clone https://github.com/akshaybabloo/dotfiles.git && cd dotfiles
```

Then run the bootstrap script:

```sh
./bootstrap.sh
```

This will:

- Detect your shell and rc file (`~/.bashrc` or `~/.zshrc`).
- Back up your rc file (e.g., `~/.bashrc.backup.YYYYMMDD_HHMMSS`).
- Append a small snippet to source the dotfiles main entry (`.main`).
- Detect your package manager and install `curl` and `git` if they're missing.
- Offer to run the updater to install and update CLI binaries via `binstall` using configs in `binary_configs/`.

When it completes, restart your terminal or source your rc file to load the changes.

### Verify

After installation, reload your shell and list available commands:

```sh
# reload current shell session
source ~/.bashrc   # or: source ~/.zshrc

# see provided commands and aliases
dotls
```

## Updating binaries later

You can re-run the updater any time to install or update the configured binaries.

```sh
dotu
```

If `~/bin` is not on your PATH, the updater will add it to your shell rc.

## What gets changed

The installer adds these lines to your shell rc:

```sh
# Gollahalli Dotfiles
. "/path/to/cloned/dotfiles/.main"
```

It also creates a timestamped backup of your original rc file in the same directory just in case anything goes wrong.

On macOS, if you use bash and only have `~/.bash_profile`, the script will remind you to source `~/.bashrc` from it. Add this to `~/.bash_profile` if prompted:

```sh
if [ -f ~/.bashrc ]; then
        . ~/.bashrc
fi
```

## Uninstall

1) Restore your rc backup or remove the added lines manually.

- Restore backup (example):
    - Move or copy `~/.bashrc.backup.YYYYMMDD_HHMMSS` back to `~/.bashrc` (or the zsh equivalent).
- Or edit your rc file and delete the block:
    ```sh
    # Gollahalli Dotfiles
    . "/path/to/cloned/dotfiles/.main"
    ```
2) Open a new terminal or `source` your rc file.
3) Optionally, remove the cloned `dotfiles` directory.

## Troubleshooting

- “Do not run this script as root!” — Run `./bootstrap.sh` as your regular user; you can still use `sudo` for commands later.
- “Unsupported shell” — Only bash and zsh are supported.
- “No supported package manager found” — Install `curl` and `git` manually, then re-run the script.
- “Dotfiles are already installed in rc” — The installer will ask whether to reinstall; choose `Yes` to re-append or `No` to keep as-is.
- `dotls: command not found` — Reload your shell: `source ~/.bashrc` or `source ~/.zshrc`, or open a new terminal.
- Binaries not available on PATH — Run `./updater.sh`; it ensures `~/bin` is on PATH.

If you hit something unexpected, feel free to file an issue on the repository.
