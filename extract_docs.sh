#!/bin/bash

function_content=""
alias_content=""
comments=""
sub_title=""

process_file() {
    local file=$1
    local type=$2
    local -n content_var=$3
    local lineno=0
    local baseURL="https://github.com/akshaybabloo/dotfiles/blob/main"

    # Add a heading to the man page content
    content_var+="# $type\n\n"

    # Determine the URL segment based on the content type
    local urlSegment=".functions" # default to functions
    if [[ $type == "Aliases" ]]; then
        urlSegment=".aliases"
    fi

    # Read the file line by line
    while IFS= read -r line; do
        ((lineno++))  # Increment line number for every line

        # Check for '## h2:' pattern first
        if [[ $line == \#\#\ h2:* ]]; then
            # Process and trim for '## h2:' lines
            trimmed_line=$(echo $line | sed 's/^## h2:[[:space:]]*//')
            sub_title+="## $trimmed_line\n"
        # Then check for '##' pattern
        elif [[ $line == \#\#* ]]; then
            # Process and trim for '##' lines
            trimmed_line=$(echo $line | sed 's/^##[[:space:]]*//')
            if [[ $trimmed_line == Usage:* ]]; then
                trimmed_line="\n**$trimmed_line**"
            fi
            comments+="$trimmed_line\n"
        elif [[ $line == function* ]] || [[ $line == alias* ]]; then
            name=$(echo $line | awk '{print $2}' | cut -d'=' -f1)
            if [[ $name == _* ]]; then
                continue
            fi
            content_var+="$sub_title\n\n### $name\n\n[<Badge type=\"tip\" text=\"source\" />]($baseURL/$urlSegment#L$lineno)\n\n$comments\n"
            comments=""
            sub_title=""
        fi
    done < "$file"
}

process_file ".functions" "Functions" function_content
process_file ".aliases" "Aliases" alias_content

# Write to separate markdown files
echo -e $function_content > $(pwd)/docs/functions-auto.md
echo -e $alias_content > $(pwd)/docs/aliases-auto.md
