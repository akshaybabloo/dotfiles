#!/bin/bash

if [ "$EUID" -eq 0 ]; then
    printf "\e[1m\e[31mDo not run this script as root!\e[0m\n"
    exit 1
fi

current_dir=$(pwd)

printf "Checking software dependencies...\n\n"
source $current_dir/install.sh

if ! grep -q ".main" ~/.bashrc; then
    printf "\n# Gollahalli Dotfiles\n. ${current_dir}/.main\n" >> ~/.bashrc
    source ~/.bashrc
fi
