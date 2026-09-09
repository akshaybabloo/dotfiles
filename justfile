default: (help)
current_path := justfile_directory()

# Help about using just in this project
@help:
    just --list

# Generates docs for the project
build-docs: docs
    pnpm run docs:build

docs:
    ./extract_docs.sh
    