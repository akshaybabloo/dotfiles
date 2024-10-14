#!/bin/bash

current_dir=$(pwd)
go_path=$HOME/go

printf "Checking if Go is installed...\n"

function install_go() {
    curl -o go.tar.gz "https://dl.google.com/go/$(curl https://go.dev/VERSION?m=text | head -n1).linux-amd64.tar.gz"
    mkdir -p $go_path
    tar -xvzf go.tar.gz -C $HOME
    rm go.tar.gz
    printf "\nexport PATH=\"\$PATH:$go_path/bin"\" >> $HOME/.bashrc
    source $HOME/.bashrc
}

if ! command -v go &> /dev/null; then
    printf "Go is not installed. Would you like to install it?\n"
    select yn in "Yes" "No"; do
        case $yn in
            Yes ) install_go; break;;
            No ) break;;
        esac
    done
fi

printf "Building updater...\n"

# Create $HOME/bin if it doesn't exist
mkdir -p $HOME/bin

# Build dotfiles-updater and move to $HOME/bin
cd $current_dir/updater
$go_path/bin/go build -o dotfiles-updater main.go
mv dotfiles-updater $HOME/bin/dotfiles-updater

printf "Updater built successfully!\n\n"

cd $current_dir

# Initial run of updater
$HOME/bin/dotfiles-updater download $current_dir/binary_configs/
