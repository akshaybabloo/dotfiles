#!/bin/bash

function _whereami() {
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

    echo $script_dir
}

current_dir=$(pwd)
github_link="https://api.github.com/repos/akshaybabloo/binstall/releases/latest"

function os_arch() {
    os=$(uname -s | tr '[:upper:]' '[:lower:]')
    arch=$(uname -m)
    case $arch in
    x86_64)
        arch="amd64"
        ;;
    arm64)
        arch="arm64"
        ;;
    esac
    echo "$os $arch"
}

function download_and_install_binstall() {
    printf "Downloading latest binstall...\n"

    # Create $HOME/bin if it doesn't exist
    mkdir -p $HOME/bin

    json=$(curl -s $github_link)

    # Check arch and os in the json
    os_arch=$(os_arch)

    # split os_arch into os and arch
    os=$(echo $os_arch | cut -d ' ' -f 1)
    arch=$(echo $os_arch | cut -d ' ' -f 2)

    download_url=$(echo $json | jq -r ".assets[] | select(.name | test(\"$os\") and test(\"$arch\")) | .browser_download_url")
    # curl -sL $download_url | tar xz -C $HOME/bin --strip-components=1 binstall
    curl -sL $download_url -o temp_archive.tar.gz
    tar xzf temp_archive.tar.gz -C $HOME/bin binstall

    # Check if $HOME/bin is in path
    if ! echo "$PATH" | grep -q "$HOME/bin"; then
        printf "Adding $HOME/bin to PATH...\n"
        echo "export PATH=\$PATH:$HOME/bin" >> ~/.bashrc
        source ~/.bashrc
    fi

    rm temp_archive.tar.gz
}

function check_for_new_updater() {
    version=$(binstall --version | cut -d ' ' -f 2)
    latest_version=$(curl -s $github_link | jq -r ".tag_name")

    if [ "$(printf '%s\n' "$version" "$latest_version" | sort -V | head -n1)" != "$latest_version" ]; then
        printf "New version of updater is available. Updating now...\n"
        download_and_install_binstall
    fi
}

printf "Checking if updater is installed...\n"

# Check if "binstall" is installed
if ! command -v binstall &>/dev/null; then
    printf "binstall is not installed. Installing it now...\n"
    # Check if "jq" is installed
    if ! command -v jq &>/dev/null; then
        printf "jq is not installed. Please install it first.\n"
        exit 1
    fi
    download_and_install_binstall
fi

# Check for new updates
check_for_new_updater

printf "Updater installed. Checking for updates...\n"

# Check for updates
binstall download $(_whereami)/binary_configs
