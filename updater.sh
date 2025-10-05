#!/bin/bash

set -euo pipefail  # Exit on error, undefined variables, pipe failures

readonly GITHUB_API="https://api.github.com/repos/akshaybabloo/binstall/releases/latest"
readonly INSTALL_DIR="$HOME/bin"
readonly BINARY_NAME="binstall"

# Color output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

log_error() {
    echo -e "${RED}Error: $1${NC}" >&2
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

function _whereami() {
    if [[ $0 == -* ]]; then
        if [[ $SHELL == */zsh ]]; then
            dirname "$ZSH_ARGZERO"
        elif [[ $SHELL == */bash ]]; then
            dirname "${BASH_SOURCE[0]}"
        else
            log_error "Unsupported shell: $SHELL"
            exit 1
        fi
    else
        dirname "${BASH_SOURCE[0]}"
    fi
}

function get_os_arch() {
    local os arch
    
    os=$(uname -s | tr '[:upper:]' '[:lower:]')
    arch=$(uname -m)
    
    case $arch in
        x86_64)
            arch="amd64"
            ;;
        aarch64|arm64)
            arch="arm64"
            ;;
        *)
            log_error "Unsupported architecture: $arch"
            return 1
            ;;
    esac
    
    echo "$os $arch"
}

function check_dependencies() {
    local missing_deps=()
    
    for cmd in curl jq tar; do
        if ! command -v "$cmd" &>/dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        log_info "Please install them and try again."
        return 1
    fi
    
    return 0
}

function add_to_path() {
    # Check if already in PATH
    if echo "$PATH" | grep -q "$INSTALL_DIR"; then
        return 0
    fi
    
    log_info "Adding $INSTALL_DIR to PATH..."
    
    # Detect shell and add to appropriate rc file
    local shell_rc=""
    if [[ $SHELL == */zsh ]]; then
        shell_rc="$HOME/.zshrc"
    elif [[ $SHELL == */bash ]]; then
        shell_rc="$HOME/.bashrc"
    else
        log_error "Unsupported shell: $SHELL"
        return 1
    fi
    
    # Add to rc file if not already there
    if ! grep -q "export PATH=.*$INSTALL_DIR" "$shell_rc" 2>/dev/null; then
        echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$shell_rc"
        log_success "Added to $shell_rc"
        log_info "Please restart your shell or run: source $shell_rc"
    fi
    
    # Add to current session
    export PATH="$PATH:$INSTALL_DIR"
}

function download_and_install_binstall() {
    log_info "Downloading latest $BINARY_NAME..."
    
    # Create install directory
    mkdir -p "$INSTALL_DIR"
    
    # Fetch release info
    local json
    if ! json=$(curl -fsSL "$GITHUB_API"); then
        log_error "Failed to fetch release information"
        return 1
    fi
    
    # Get OS and architecture
    local os_arch_info
    if ! os_arch_info=$(get_os_arch); then
        return 1
    fi
    
    local os arch
    os=$(echo "$os_arch_info" | cut -d ' ' -f 1)
    arch=$(echo "$os_arch_info" | cut -d ' ' -f 2)
    
    log_info "Detected: $os $arch"
    
    # Get download URL
    local download_url
    download_url=$(echo "$json" | jq -r ".assets[] | select(.name | test(\"$os\") and test(\"$arch\")) | .browser_download_url")
    
    if [[ -z $download_url || $download_url == "null" ]]; then
        log_error "No release found for $os $arch"
        return 1
    fi
    
    log_info "Downloading from: $download_url"
    
    # Download and extract
    local temp_archive="$INSTALL_DIR/temp_binstall.tar.gz"
    
    if ! curl -fsSL "$download_url" -o "$temp_archive"; then
        log_error "Failed to download archive"
        rm -f "$temp_archive"
        return 1
    fi
    
    if ! tar xzf "$temp_archive" -C "$INSTALL_DIR" "$BINARY_NAME"; then
        log_error "Failed to extract archive"
        rm -f "$temp_archive"
        return 1
    fi
    
    rm -f "$temp_archive"
    
    # Make executable
    chmod +x "$INSTALL_DIR/$BINARY_NAME"
    
    # Add to PATH
    add_to_path
    
    log_success "$BINARY_NAME installed successfully!"
    return 0
}

function get_installed_version() {
    if ! command -v "$BINARY_NAME" &>/dev/null; then
        echo ""
        return 1
    fi
    
    "$BINARY_NAME" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -n1
}

function get_latest_version() {
    local json
    if ! json=$(curl -fsSL "$GITHUB_API"); then
        log_error "Failed to fetch latest version"
        return 1
    fi
    
    echo "$json" | jq -r ".tag_name" | sed 's/^v//'
}

function check_for_updates() {
    local current_version latest_version
    
    current_version=$(get_installed_version)
    if [[ -z $current_version ]]; then
        log_error "Could not determine installed version"
        return 1
    fi
    
    log_info "Current version: $current_version"
    
    latest_version=$(get_latest_version)
    if [[ -z $latest_version ]]; then
        return 1
    fi
    
    log_info "Latest version: $latest_version"
    
    # Compare versions using sort -V
    if [[ $current_version == "$latest_version" ]]; then
        log_success "$BINARY_NAME is up to date!"
        return 0
    fi
    
    if [[ $(printf '%s\n' "$current_version" "$latest_version" | sort -V | head -n1) == "$current_version" ]]; then
        log_info "New version available: $latest_version"
        log_info "Updating..."
        download_and_install_binstall
    else
        log_success "$BINARY_NAME is up to date!"
    fi
}

# Main execution
main() {
    log_info "Checking if $BINARY_NAME is installed..."
    
    # Check dependencies
    if ! check_dependencies; then
        exit 1
    fi
    
    # Install if not present
    if ! command -v "$BINARY_NAME" &>/dev/null; then
        log_info "$BINARY_NAME is not installed. Installing now..."
        if ! download_and_install_binstall; then
            log_error "Installation failed"
            exit 1
        fi
    fi
    
    # Check for updates
    log_info "Checking for updates..."
    if ! check_for_updates; then
        log_error "Update check failed"
        exit 1
    fi
    
    # Run binstall with config
    local script_dir
    script_dir=$(_whereami)
    local config_dir="$script_dir/binary_configs"
    
    if [[ ! -d $config_dir ]]; then
        log_error "Config directory not found: $config_dir"
        exit 1
    fi
    
    log_info "Running binstall with configs from: $config_dir"
    "$BINARY_NAME" download "$config_dir"
}

main "$@"
