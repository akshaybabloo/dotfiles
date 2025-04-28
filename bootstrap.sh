#!/bin/bash

if [ "$EUID" -eq 0 ]; then
    printf "\e[1m\e[31mDo not run this script as root!\e[0m\n"
    exit 1
fi

current_dir=$(pwd)

printf "Checking software dependencies...\n\n"
source $current_dir/install.sh

printf "Install updater?\n"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) source $current_dir/updater.sh; break;;
        No ) break;;
    esac
done

printf "\n"

# Installing basic dependencies
printf "Installing basic dependencies...\n"
sudo apt install gnome-keyring curl

if ! grep -q ".main" ~/.bashrc; then
    printf "\n# Gollahalli Dotfiles\n. ${current_dir}/.main\n" >> ~/.bashrc
    source ~/.bashrc
fi

echo "Dotfiles installed successfully!"
printf "\n\n"
echo "If you are using ~/.bash_profile, please add the following lines to it:"
printf "\nif [ -f ~/.bashrc ]; then\n    . ~/.bashrc\nfi\n"
