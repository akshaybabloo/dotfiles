default: (help)
current_path := justfile_directory()

# Help about using just in this project
@help:
    just --list

# Generates docs for the project
docs:
    ./extract_docs.sh
    cd {{current_path}}/docs && bun run docs:build
    