default: (help)
current_dir := `pwd`

# Help about using just in this project
@help:
    just --list

# Generates docs for the project
docs:
    #!/usr/bin/env bash
    cd {{current_dir}}/docs
    ./extract_man.sh
    bun run docs:build
    cd {{current_dir}}
    