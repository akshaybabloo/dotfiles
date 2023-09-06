#!/bin/bash

declare python_dependencies=("httpie" "eza" "tree")
declare binary_dependencies=("git", "conda")

commands_to_install=()

# Check if python is installed
if ! command -v python3 &> /dev/null; then
    commands_to_install+=("python3")
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    commands_to_install+=("python3-pip")
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    commands_to_install+=("git")
fi

# Check if httpie is installed
if ! command -v http &> /dev/null; then
    commands_to_install+=("httpie")
fi

# Check if eza is installed
if ! command -v eza &> /dev/null; then
    commands_to_install+=("eza")
fi

# Check if tree is installed
if ! command -v tree &> /dev/null; then
    commands_to_install+=("tree")
fi

# If there are commands to install, install them
if [ ${#commands_to_install[@]} -gt 0 ]; then
    echo "Following commands are missing: ${commands_to_install[@]}..."
    # sudo apt-get update
    # sudo apt-get install ${commands_to_install[@]}
fi
