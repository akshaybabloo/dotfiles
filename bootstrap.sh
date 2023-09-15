#!/bin/bash

current_dir=$(pwd)

echo "Checking software dependencies..."
source $current_dir/install.sh

if ! grep -q ".main" ~/.bashrc; then
    echo ". ${current_dir}/.main" >> ~/.bashrc
    source ~/.bashrc
fi
