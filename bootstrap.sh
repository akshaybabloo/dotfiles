#!/bin/bash

current_dir=$(pwd)

echo "Checking software dependencies..."
source $current_dir/install.sh

if ! grep -q ".yolo" ~/.bashrc; then
    echo ". ${current_dir}/.yolo" >> ~/.bashrc
    source ~/.bashrc
fi
