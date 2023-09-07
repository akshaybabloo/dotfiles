#!/bin/bash

declare -a python_dependencies=("httpie")
declare -a binary_dependencies=("git" "conda" "eza" "tree")

python_commands_to_install=()
binary_commands_to_install=()

# Check if python is installed
if ! command -v python3 &> /dev/null; then
    binary_commands_to_install+=("python3")
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    binary_commands_to_install+=("python3-pip")
fi

# Check for binary dependencies
for cmd in "${binary_dependencies[@]}"; do
    if ! command -v $cmd &> /dev/null; then
        binary_commands_to_install+=($cmd)
    fi
done

# Check for python dependencies
for cmd in "${python_dependencies[@]}"; do
    if ! pip3 show $cmd &> /dev/null; then
        python_commands_to_install+=($cmd)
    fi
done

# If there are commands to install, print them at the end
if [ ${#binary_commands_to_install[@]} -gt 0 ] || [ ${#python_commands_to_install[@]} -gt 0 ]; then
    echo "Missing dependencies:"
    
    if [ ${#binary_commands_to_install[@]} -gt 0 ]; then
        echo "Binary dependencies:"
        for dep in "${binary_commands_to_install[@]}"; do
            echo "     $dep"
        done
        # sudo apt-get update
        # sudo apt-get install ${binary_commands_to_install[@]}
    fi

    if [ ${#python_commands_to_install[@]} -gt 0 ]; then
        echo "Python dependencies:"
        for dep in "${python_commands_to_install[@]}"; do
            echo "     $dep"
        done
        # pip3 install ${python_commands_to_install[@]}
    fi
else
    echo "No missing dependencies found."
fi
