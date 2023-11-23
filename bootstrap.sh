#!/bin/bash

current_dir=$(pwd)

printf "Checking software dependencies...\n\n"
source $current_dir/install.sh

if ! grep -q ".main" ~/.bashrc; then
    printf "\n# Gollahalli Dotfiles\n. ${current_dir}/.main\n" >> ~/.bashrc
    source ~/.bashrc
fi
