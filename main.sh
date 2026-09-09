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
for file in "$script_dir"/.{aliases,functions}; do
    echo "Sourcing $file..."
    if [ -r "$file" ] && [ -f "$file" ]; then
        source "$file"
    fi
done
unset file
