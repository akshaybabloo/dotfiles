#!/bin/bash

set -euo pipefail  # Exit on error, undefined variables, pipe failures

# Configuration
readonly FUNCTIONS_FILE="${1:-.functions}"
readonly ALIASES_FILE="${2:-.aliases}"
readonly OUTPUT_DIR="${3:-$(pwd)/docs}"
readonly BASE_URL="https://github.com/akshaybabloo/dotfiles/blob/main"

function_content=""
alias_content=""
comments=""
sub_title=""

# Colors for output
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

process_file() {
    local file=$1
    local type=$2
    local -n content_var=$3
    local lineno=0

    # Check if file exists
    if [[ ! -f "$file" ]]; then
        log_error "File '$file' not found"
        return 1
    fi

    # Add a heading to the man page content
    content_var+="# $type\n\n"

    # Determine the URL segment based on the content type
    local urlSegment="${file}"
    
    log_info "Processing $type from $file..."

    # Read the file line by line
    while IFS= read -r line; do
        ((lineno++))

        # Check for '## h2:' pattern first
        if [[ $line == \#\#\ h2:* ]]; then
            # Process and trim for '## h2:' lines
            trimmed_line=$(echo "$line" | sed 's/^## h2:[[:space:]]*//')
            sub_title+="## $trimmed_line\n"
        # Then check for '##' pattern
        elif [[ $line == \#\#* ]]; then
            # Process and trim for '##' lines
            trimmed_line=$(echo "$line" | sed 's/^##[[:space:]]*//')
            
            # Bold certain patterns
            if [[ $trimmed_line == Usage:* ]] || \
               [[ $trimmed_line == Options:* ]] || \
               [[ $trimmed_line == Examples:* ]]; then
                trimmed_line="\n**$trimmed_line**\n"
            fi
            
            comments+="$trimmed_line\n"
        elif [[ $line == function* ]] || [[ $line == alias* ]]; then
            # Extract function/alias name
            if [[ $line == function* ]]; then
                name=$(echo "$line" | awk '{print $2}' | sed 's/().*//')
            else
                name=$(echo "$line" | awk '{print $2}' | cut -d'=' -f1)
            fi
            
            # Skip private functions (starting with _)
            if [[ $name == _* ]]; then
                # Output sub_title if present, so h2 headings aren't lost
                if [[ -n $sub_title ]]; then
                    content_var+="$sub_title\n\n"
                fi
                comments=""
                sub_title=""
                continue
            fi
            
            # Only add entry if there are comments
            if [[ -n $comments || -n $sub_title ]]; then
                content_var+="$sub_title\n\n### $name\n\n"
                content_var+="[<Badge type=\"tip\" text=\"source\" />]($BASE_URL/$urlSegment#L$lineno)\n\n"
                content_var+="$comments\n"
            fi
            
            # Reset for next function
            comments=""
            sub_title=""
        fi
    done < "$file"
    
    return 0
}

# Main execution
main() {
    # Create output directory if it doesn't exist
    if [[ ! -d "$OUTPUT_DIR" ]]; then
        log_info "Creating output directory: $OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
    fi

    local functions_output="$OUTPUT_DIR/functions-auto.md"
    local aliases_output="$OUTPUT_DIR/aliases-auto.md"

    # Check if output files exist and warn
    if [[ -f "$functions_output" ]] || [[ -f "$aliases_output" ]]; then
        log_info "Output files will be overwritten"
    fi

    # Process files
    if ! process_file "$FUNCTIONS_FILE" "Functions" function_content; then
        log_error "Failed to process functions file"
        exit 1
    fi

    if ! process_file "$ALIASES_FILE" "Aliases" alias_content; then
        log_error "Failed to process aliases file"
        exit 1
    fi

    # Write to separate markdown files
    if [[ -n $function_content ]]; then
        echo -e "$function_content" > "$functions_output"
        log_success "Generated: $functions_output"
    else
        log_error "No function content generated"
        exit 1
    fi

    if [[ -n $alias_content ]]; then
        echo -e "$alias_content" > "$aliases_output"
        log_success "Generated: $aliases_output"
    else
        log_error "No alias content generated"
        exit 1
    fi

    log_success "Documentation generation complete!"
}

# Run main function
main "$@"
