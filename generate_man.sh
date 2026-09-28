#!/bin/bash

# Generates man pages from the `##` doc comments in functions.sh and aliases.sh
# (the same comments extract_docs.sh turns into the website docs).
#
# Output:
#   <out_dir>/man1/<name>.1     one page per documented function/alias
#   <out_dir>/man7/dotfiles.7   overview of everything, grouped by section
#
# Usage: generate_man.sh <out_dir> [functions.sh] [aliases.sh]

set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
readonly OUT_DIR="${1:?Usage: generate_man.sh <out_dir> [functions.sh] [aliases.sh]}"
readonly FUNCTIONS_FILE="${2:-$script_dir/functions.sh}"
readonly ALIASES_FILE="${3:-$script_dir/aliases.sh}"

for file in "$FUNCTIONS_FILE" "$ALIASES_FILE"; do
    if [[ ! -f "$file" ]]; then
        echo "Error: File '$file' not found" >&2
        exit 1
    fi
done

# Build into a temp dir next to the target and swap it in at the end, so pages
# for removed functions disappear and readers never see a half-written tree
mkdir -p "$(dirname "$OUT_DIR")"
tmp_dir=$(mktemp -d "${OUT_DIR%/}.tmp.XXXXXX")
trap 'rm -rf "$tmp_dir"' EXIT
mkdir -p "$tmp_dir/man1" "$tmp_dir/man7"

# Portable awk (works with gawk, mawk and macOS awk)
awk -v out="$tmp_dir" -v functions_file="$FUNCTIONS_FILE" '
# Replace every literal occurrence of `from` in `s` (no regex/backslash surprises)
function rep(s, from, to,    r, i) {
    r = ""
    while ((i = index(s, from)) > 0) {
        r = r substr(s, 1, i - 1) to
        s = substr(s, i + length(from))
    }
    return r s
}

# Wrap text between pairs of `delim` in bold
function bold_pairs(s, delim,    r, i, j, rest) {
    r = ""
    while ((i = index(s, delim)) > 0) {
        rest = substr(s, i + length(delim))
        j = index(rest, delim)
        if (j == 0) break
        r = r substr(s, 1, i - 1) "\\fB" substr(rest, 1, j - 1) "\\fR"
        s = substr(rest, j + length(delim))
    }
    return r s
}

# Convert the markdown-ish comment text into troff
function fmt(s) {
    s = rep(s, "\\", "\\e")
    s = rep(s, "-", "\\-")
    # [text](url) -> text (url)
    while (match(s, /\[[^]]*\]\([^)]*\)/)) {
        link = substr(s, RSTART, RLENGTH)
        sep = index(link, "](")
        s = substr(s, 1, RSTART - 1) substr(link, 2, sep - 2) " (" substr(link, sep + 2, length(link) - sep - 2) ")" substr(s, RSTART + RLENGTH)
    }
    s = bold_pairs(s, "**")
    s = bold_pairs(s, "`")
    # A leading . or apostrophe would be read as a troff request
    if (s ~ /^[.\047]/) s = "\\&" s
    return s
}

function trim(s) {
    sub(/^[ \t]+/, "", s)
    sub(/[ \t]+$/, "", s)
    return s
}

function reset_item() {
    n = 0; synopsis = ""; summary = ""; summary_done = 0; in_aside = 0
}

# Record one comment line of the current item
function add_comment(line,    t) {
    t = trim(line)
    if (t ~ /^<Aside/) { in_aside = 1 }
    else if (t ~ /^<\/Aside>/) { in_aside = 0 }
    else if (t ~ /^Usage:/) { synopsis = trim(substr(t, 7)); if (summary != "") summary_done = 1; return }
    else if (!summary_done && !in_aside && t != "" && t !~ /^(Options|Examples):/ && t !~ /^[->] /) {
        # The summary is the first paragraph of plain text, which may wrap over several lines
        summary = (summary == "") ? t : summary " " t
    } else if (summary != "") { summary_done = 1 }
    lines[++n] = line
}

function write_page(name, kind, definition,    file, i, line, t, title, mode, tag, desc) {
    file = out "/man1/" name ".1"
    print ".TH \"" toupper(name) "\" 1 \"\" \"dotfiles\" \"Dotfiles Manual\"" > file
    print ".SH NAME" > file
    print fmt(name) " \\- " fmt(short) > file
    if (synopsis != "") {
        print ".SH SYNOPSIS" > file
        print fmt(synopsis) > file
    }
    print ".SH DESCRIPTION" > file
    mode = ""
    for (i = 1; i <= n; i++) {
        line = lines[i]
        t = trim(line)
        if (t == "") { print ".PP" > file; continue }
        if (t ~ /^<Aside/) {
            title = "Note"
            if (match(t, /title="[^"]*"/)) title = substr(t, RSTART + 7, RLENGTH - 8)
            print ".PP" > file
            print "\\fB" fmt(title) "\\fR" > file
            print ".RS" > file
            continue
        }
        if (t ~ /^<\/Aside>/) { print ".RE" > file; print ".PP" > file; continue }
        if (t ~ /^Options:/) { print ".SH OPTIONS" > file; mode = "list"; continue }
        if (t ~ /^Examples:/) { print ".SH EXAMPLES" > file; mode = "list"; continue }
        if (t ~ /^> /) { t = substr(t, 3) }
        if (t ~ /^- /) { print ".IP \\(bu 2" > file; print fmt(substr(t, 3)) > file; continue }
        # Indented "tag    description" rows under Options/Examples
        if (mode == "list" && line ~ /^[ \t]/) {
            if (match(t, /  +/)) {
                # Extract both halves before fmt(), which calls match() and resets RSTART
                tag = substr(t, 1, RSTART - 1)
                desc = substr(t, RSTART + RLENGTH)
                print ".TP" > file
                print fmt(tag) > file
                print fmt(desc) > file
            } else {
                print ".TP" > file
                print fmt(t) > file
            }
            continue
        }
        if (mode == "list") { print ".PP" > file; mode = "" }
        print fmt(t) > file
    }
    if (kind == "alias" && definition != "") {
        print ".SH ALIAS" > file
        print "Expands to \\fB" fmt(definition) "\\fR" > file
    }
    print ".SH SEE ALSO" > file
    print "\\fBdotfiles\\fR(7)" > file
    close(file)
}

FNR == 1 { kind = (FILENAME == functions_file) ? "function" : "alias"; section = ""; reset_item() }

/^## h2:/ {
    section = trim(substr($0, 7))
    next
}

/^##/ {
    line = substr($0, 3)
    sub(/^ /, "", line)
    add_comment(line)
    next
}

/^function / || /^alias / {
    definition = ""
    if (kind == "function") {
        name = $2
        sub(/\(.*/, "", name)
    } else {
        rest = $0
        sub(/^alias( --)? /, "", rest)
        eq = index(rest, "=")
        name = substr(rest, 1, eq - 1)
        definition = substr(rest, eq + 1)
        # Keep only the quoted value, dropping any trailing comment
        if (match(definition, /^"[^"]*"/) || match(definition, /^\047[^\047]*\047/)) {
            definition = substr(definition, 2, RLENGTH - 2)
        }
    }

    # Skip private functions and undocumented items
    if (name ~ /^_/ || n == 0) { reset_item(); next }

    # First sentence of the summary paragraph
    short = summary
    if ((i = index(short, ". ")) > 0) short = substr(short, 1, i)
    # "`7zx` extracts ..." -> "extracts ..."
    if (index(short, "`" name "` ") == 1) short = substr(short, length(name) + 4)

    # Names like "..", "~" or "-" cannot be page names; they only go in the overview
    has_page = (name ~ /^[A-Za-z0-9_][A-Za-z0-9_.+-]*$/)
    if (has_page) write_page(name, kind, definition)

    count[kind]++
    idx = count[kind]
    item_name[kind, idx] = name
    item_short[kind, idx] = short
    item_section[kind, idx] = section
    item_page[kind, idx] = has_page
    item_def[kind, idx] = definition

    reset_item()
}

function write_overview_list(kind, file,    i, last) {
    last = ""
    for (i = 1; i <= count[kind]; i++) {
        if (item_section[kind, i] != last) {
            last = item_section[kind, i]
            if (last != "") print ".SS " fmt(last) > file
        }
        print ".TP" > file
        if (item_page[kind, i]) print "\\fB" fmt(item_name[kind, i]) "\\fR(1)" > file
        else print "\\fB" fmt(item_name[kind, i]) "\\fR" > file
        if (item_short[kind, i] != "") print fmt(item_short[kind, i]) > file
        else print "Expands to \\fB" fmt(item_def[kind, i]) "\\fR" > file
    }
}

END {
    file = out "/man7/dotfiles.7"
    print ".TH \"DOTFILES\" 7 \"\" \"dotfiles\" \"Dotfiles Manual\"" > file
    print ".SH NAME" > file
    print "dotfiles \\- aliases and functions provided by the dotfiles" > file
    print ".SH DESCRIPTION" > file
    print "Run \\fBman\\fR \\fIname\\fR for details on any entry marked (1)." > file
    print "Run \\fBdot\\fR for the dotfiles helper commands." > file
    print ".SH FUNCTIONS" > file
    write_overview_list("function", file)
    print ".SH ALIASES" > file
    write_overview_list("alias", file)
    close(file)
}
' "$FUNCTIONS_FILE" "$ALIASES_FILE"

# Timestamp used by main.sh to decide whether the pages need rebuilding
touch "$tmp_dir/.stamp"

rm -rf "$OUT_DIR"
mv "$tmp_dir" "$OUT_DIR"
trap - EXIT
