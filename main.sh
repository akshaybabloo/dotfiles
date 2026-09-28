#!/bin/bash

if [[ $0 == -* ]]; then
    if [[ $SHELL == */zsh ]]; then
        script_dir=$(dirname "$ZSH_ARGZERO")
    elif [[ $SHELL == */bash ]]; then
        script_dir=$(dirname "${BASH_SOURCE[0]}")
    else
        echo "Unsupported shell: $SHELL"
        exit 1
    fi
else
    script_dir=$(dirname "${BASH_SOURCE[0]}")
fi

# Source all files
for file in "$script_dir"/{aliases.sh,functions.sh}; do
    if [ -r "$file" ] && [ -f "$file" ]; then
        source "$file"
    fi
done
unset file

# Man pages generated from the doc comments, e.g. `man 7zx` or `man dotfiles`
_dot_man_dir="${XDG_DATA_HOME:-$HOME/.local/share}/dotfiles/man"

# Rebuild in the background whenever the documented files (or the generator) change,
# e.g. after `dotu` pulls updates or a local edit
if [[ ! -f "$_dot_man_dir/.stamp" \
    || "$script_dir/functions.sh" -nt "$_dot_man_dir/.stamp" \
    || "$script_dir/aliases.sh" -nt "$_dot_man_dir/.stamp" \
    || "$script_dir/generate_man.sh" -nt "$_dot_man_dir/.stamp" ]]; then
    (bash "$script_dir/generate_man.sh" "$_dot_man_dir" >/dev/null 2>&1 &)
fi

# A leading ":" keeps the system search path first, so these never shadow real man pages
case ":${MANPATH:-}:" in
    *":$_dot_man_dir:"*) ;;
    *) export MANPATH="${MANPATH:-}:$_dot_man_dir" ;;
esac
unset _dot_man_dir
