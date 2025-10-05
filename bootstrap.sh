#!/bin/bash

set -e  # Exit on error

# Color codes
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

log_error() {
    echo -e "${RED}Error: $1${NC}" >&2
}

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if running as root
if [[ "$EUID" -eq 0 ]]; then
    log_error "Do not run this script as root!"
    exit 1
fi

# Get script directory
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly DOTFILES_MAIN="$SCRIPT_DIR/.main"

# Detect shell RC file
detect_shell_rc() {
    if [[ -n "$ZSH_VERSION" ]]; then
        echo "$HOME/.zshrc"
    elif [[ -n "$BASH_VERSION" ]]; then
        echo "$HOME/.bashrc"
    else
        log_error "Unsupported shell. Please use bash or zsh."
        exit 1
    fi
}

# Detect package manager
detect_package_manager() {
    if command -v apt &>/dev/null; then
        echo "apt"
    elif command -v dnf &>/dev/null; then
        echo "dnf"
    elif command -v yum &>/dev/null; then
        echo "yum"
    elif command -v pacman &>/dev/null; then
        echo "pacman"
    elif command -v brew &>/dev/null; then
        echo "brew"
    else
        log_error "No supported package manager found"
        return 1
    fi
}

# Install basic dependencies
install_dependencies() {
    local pkg_manager
    pkg_manager=$(detect_package_manager)
    
    log_info "Detected package manager: $pkg_manager"
    log_info "Installing basic dependencies..."
    
    case "$pkg_manager" in
        apt)
            sudo apt update && sudo apt install -y curl git
            ;;
        dnf|yum)
            sudo "$pkg_manager" install -y curl git
            ;;
        pacman)
            sudo pacman -Sy --noconfirm curl git
            ;;
        brew)
            brew install curl git
            ;;
        *)
            log_error "Unsupported package manager"
            return 1
            ;;
    esac
    
    log_success "Dependencies installed"
}

# Check if dotfiles are already installed
is_already_installed() {
    local shell_rc=$1
    
    if [[ ! -f "$shell_rc" ]]; then
        return 1
    fi
    
    grep -qF "$DOTFILES_MAIN" "$shell_rc"
}

# Backup shell RC file
backup_shell_rc() {
    local shell_rc=$1
    local backup_file="${shell_rc}.backup.$(date +%Y%m%d_%H%M%S)"
    
    if [[ -f "$shell_rc" ]]; then
        cp "$shell_rc" "$backup_file"
        log_success "Backed up $shell_rc to $backup_file"
    fi
}

# Install dotfiles to shell RC
install_dotfiles() {
    local shell_rc
    shell_rc=$(detect_shell_rc)
    
    log_info "Installing dotfiles to $shell_rc"
    
    # Check if .main exists
    if [[ ! -f "$DOTFILES_MAIN" ]]; then
        log_error ".main file not found at $DOTFILES_MAIN"
        exit 1
    fi
    
    # Check if already installed
    if is_already_installed "$shell_rc"; then
        log_warning "Dotfiles are already installed in $shell_rc"
        echo -n "Do you want to reinstall? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            log_info "Skipping installation"
            return 0
        fi
    fi
    
    # Backup existing RC file
    backup_shell_rc "$shell_rc"
    
    # Add dotfiles to RC file
    {
        echo ""
        echo "# Gollahalli Dotfiles"
        echo ". \"$DOTFILES_MAIN\""
    } >> "$shell_rc"
    
    log_success "Dotfiles added to $shell_rc"
}

# Run updater script
run_updater() {
    local updater_script="$SCRIPT_DIR/updater.sh"
    
    if [[ ! -f "$updater_script" ]]; then
        log_warning "updater.sh not found, skipping"
        return 0
    fi
    
    echo ""
    log_info "Do you want to run the updater script?"
    select yn in "Yes" "No"; do
        case $yn in
            Yes)
                log_info "Running updater..."
                if bash "$updater_script"; then
                    log_success "Updater completed successfully"
                else
                    log_error "Updater failed"
                    return 1
                fi
                break
                ;;
            No)
                log_info "Skipping updater"
                break
                ;;
        esac
    done
}

# Main installation
main() {
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║   Gollahalli Dotfiles Installation     ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
    
    # Install dependencies
    if ! install_dependencies; then
        log_error "Failed to install dependencies"
        exit 1
    fi
    
    echo ""
    
    # Install dotfiles
    if ! install_dotfiles; then
        log_error "Failed to install dotfiles"
        exit 1
    fi
    
    echo ""
    
    # Run updater (optional)
    run_updater
    
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║     Installation completed! 🎉         ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
    
    local shell_rc
    shell_rc=$(detect_shell_rc)
    
    log_info "Next steps:"
    echo "  1. Restart your terminal or run: source $shell_rc"
    echo "  2. Run 'dotls' to see all available commands"
    echo ""
    
    # Check for .bash_profile on macOS/Linux
    if [[ -f "$HOME/.bash_profile" ]] && [[ ! -f "$HOME/.bashrc" || ! $(grep -q ".bashrc" "$HOME/.bash_profile") ]]; then
        log_warning "You have a .bash_profile file"
        echo "Add the following to ~/.bash_profile to load .bashrc:"
        echo ""
        echo "  if [ -f ~/.bashrc ]; then"
        echo "      . ~/.bashrc"
        echo "  fi"
        echo ""
    fi
}

# Run main function
main "$@"
