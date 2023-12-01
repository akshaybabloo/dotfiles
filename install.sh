#!/bin/bash

# Declare associative arrays
declare -A python_dependencies
declare -A binary_dependencies

# Populate the associative arrays
python_dependencies[httpie]="pip install httpie"

binary_dependencies[brew]="curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | bash"
binary_dependencies[git]="brew install git"
binary_dependencies[rustup]="curl https://sh.rustup.rs -sSf | sh"
binary_dependencies[conda]="brew install miniconda"
binary_dependencies[eza]="cargo install eza"
binary_dependencies[tree]="brew install tree"
binary_dependencies[bat]="brew install bat"
binary_dependencies[btop]="brew install btop"
binary_dependencies[fs_rs]="cargo install fs_rs"

# Flag to track if any dependency is missing
any_missing=false

# Function to check and print missing dependencies
check_dependencies() {
    local -n array=$1
    local has_missing=false

    for key in "${!array[@]}"; do
        if ! command -v "$key" &>/dev/null; then
            if [ "$has_missing" = false ]; then
                if [ "$any_missing" = false ]; then
                    echo "Here are some missing dependencies"
                    echo "----------------------------------"
                    any_missing=true
                fi
                echo -e "\n$2:"
                has_missing=true
            fi
            echo "    $key - ${array[$key]}"
        fi
    done
}

# Check and print missing dependencies
check_dependencies python_dependencies "Python Dependencies"
check_dependencies binary_dependencies "Binary Dependencies"

# Final message if no dependencies are missing
if [ "$any_missing" = false ]; then
    echo -e "All dependencies are installed \U1F389"
fi
