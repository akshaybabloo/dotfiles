#!/bin/bash

function_content=""
alias_content=""
comments=""

process_file() {
    local file=$1
    local type=$2
    local -n content_var=$3

    # Add a heading to the man page content
    content_var+="# $type\n\n"

    # Read the file line by line
    while IFS= read -r line; do
        # If the line starts with ##, it's a comment. Add it to the comments variable
        if [[ $line == \#\#* ]]; then
            # Trim the ## and space
            trimmed_line=$(echo $line | sed 's/^##[[:space:]]*//')
            # If the trimmed line starts with "Usage:", add a newline before it and make it bold
            if [[ $trimmed_line == Usage:* ]]; then
                trimmed_line="\n**$trimmed_line**"
            fi
            comments+="$trimmed_line\n"
        # If the line starts with function or alias, it's a declaration. Extract the name and add it to the man page content
        elif [[ $line == function* ]] || [[ $line == alias* ]]; then
            name=$(echo $line | awk '{print $2}' | cut -d'=' -f1)
            content_var+="## $name\n\n$comments\n"
            # Reset comments
            comments=""
        fi
    done < "$file"
}

process_file ".functions" "Functions" function_content
process_file ".aliases" "Aliases" alias_content

# Write to separate markdown files
echo -e $function_content > $(pwd)/docs/functions-auto.md
echo -e $alias_content > $(pwd)/docs/aliases-auto.md
