#!/bin/bash

man_page_content=""
comments=""

process_file() {
    local file=$1
    local type=$2

    # Add a heading to the man page content
    man_page_content+="## $type\n\n"

    # Read the file line by line
    while IFS= read -r line; do
        # If the line starts with ##, it's a comment. Add it to the comments variable
        if [[ $line == \#\#* ]]; then
            # Trim the ## and space
            trimmed_line=$(echo $line | sed 's/^##[[:space:]]*//')
            comments+="$trimmed_line\n"
        # If the line starts with function or alias, it's a declaration. Extract the name and add it to the man page content
        elif [[ $line == function* ]] || [[ $line == alias* ]]; then
            name=$(echo $line | awk '{print $2}' | cut -d'=' -f1)
            man_page_content+="### $name\n\n$comments\n"
            # Reset comments
            comments=""
        fi
    done < "$file"
}

process_file ".functions" "Functions"
process_file ".aliases" "Aliases"

echo -e $man_page_content > $(pwd)/docs/help.md
