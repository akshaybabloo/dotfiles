"""
Installs third party binaries and keeps track of their versions.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

HOME_BIN = Path.home().joinpath("bin")


@dataclass
class Files:
    name: str
    exists: bool = False

    def __post_init__(self):
        if not self.name:
            raise ValueError("Name cannot be empty")


@dataclass
class SHAInfo:
    url: str
    type: str

    def __post_init__(self):
        # Example validation: Ensure sha_type is one of the expected values
        if self.type not in ["SHA-1", "SHA-256", "SHA-512"]:
            raise ValueError(
                f"sha_type must be one of 'SHA-1', 'SHA-256', 'SHA-512', not {self.type}"
            )


@dataclass
class Binaries:
    name: str
    url: str
    files: List[Files]
    sha: Optional[SHAInfo] = None
    description: str = ""

    def __post_init__(self):
        # Validate name is not empty
        if not self.name:
            raise ValueError("Name cannot be empty")

        # Validate URL format (this is a simplistic check; consider using regex for real URL validation)
        if not self.url.startswith("http://") and not self.url.startswith("https://"):
            raise ValueError("URL must start with 'http://' or 'https://'")

        # Validate that files is a list with at least one entry
        if not self.files or not isinstance(self.files, list):
            raise ValueError("files must be a non-empty list")


binaries: List[Binaries] = [
    Binaries(
        name="rclone",
        url="https://",
        sha=None,
        files=[Files(name="rclone")],
    ),
    Binaries(
        name="Fs CLI",
        url="https://",
        sha=None,
        files=[Files(name="fs_rs")],
    ),
    Binaries(
        name="7-Zip CLI",
        url="https://",
        sha=None,
        files=[Files(name="7zzs")],
    ),
    Binaries(
        name="caddy",
        url="https://",
        sha=None,
        files=[Files(name="caddy")],
    ),
    Binaries(
        name="WebP",
        url="https://",
        sha=None,
        files=[Files(name="cwebp"), Files(name="gif2webp")],
    ),
    Binaries(
        name="d2",
        url="https://",
        sha=None,
        files=[Files(name="d2")],
    ),
    Binaries(
        name="ffmpeg",
        url="https://",
        sha=None,
        files=[Files(name="ffmpeg"), Files(name="ffprobe")],
    ),
    Binaries(
        name="Git Alias",
        url="https://",
        sha=None,
        files=[Files(name="git-alias")],
    ),
    Binaries(
        name="Hugo",
        url="https://",
        sha=None,
        files=[Files(name="hugo")],
    ),
    Binaries(
        name="Just",
        url="https://",
        sha=None,
        files=[Files(name="just")],
    ),
    Binaries(
        name="Mage",
        url="https://",
        sha=None,
        files=[Files(name="mage")],
    ),
    Binaries(
        name="Oh My Posh",
        url="https://",
        sha=None,
        files=[
            Files(name="oh-my-posh"),
            Files(name="oh-my-posh.json"),
            Files(name="themes/"),
        ],
    ),
    Binaries(
        name="Typst",
        url="https://",
        sha=None,
        files=[Files(name="typst")],
    ),
    Binaries(
        name="DNode",
        url="https://",
        sha=None,
        files=[Files(name="dnode")],
    ),
]


def is_binary_installed() -> List[Binaries]:
    """
    Check if the binaries are installed in the home bin directory.

    :return: List of Binaries objects with the `exists` attribute updated
    """
    for binary in binaries:
        for file in binary.files:
            file.exists = HOME_BIN.joinpath(file.name).exists()
    return binaries


def binaries_to_table(binaries: List[Binaries]) -> str:
    headers = ["Binary Name", "File Name", "Exists"]
    col_widths = {
        "Binary Name": max(max((len(b.name) for b in binaries), default=0), len(headers[0])),
        "File Name": max(max((len(f.name) for b in binaries for f in b.files), default=0), len(headers[1])),
        "Exists": len(headers[2]) + 2  # Plus 2 for padding around [x] or [ ]
    }

    separator = "+" + "+".join(["-" * (col_widths[header] + 2) for header in headers]) + "+"
    header_row = "|" + "|".join([f" {header.center(col_widths[header])} " for header in headers]) + "|"
    table = [separator, header_row, separator]

    for binary in binaries:
        binary_name_displayed = False
        if not binary.files:  # Handle binaries with no files
            empty_row = "|" + f" {binary.name.ljust(col_widths['Binary Name'])} " + \
                        "|" + " " * col_widths['File Name'] + \
                        "|" + " " * col_widths['Exists'] + "|"
            table.append(empty_row)
            table.append(separator)
        for file in binary.files:
            binary_name = binary.name if not binary_name_displayed else ""
            exists_marker = "[x]" if file.exists else "[ ]"
            data_row = "|" + f" {binary_name.ljust(col_widths['Binary Name'])} " + \
                       "|" + f" {file.name.ljust(col_widths['File Name'])} " + \
                       "|" + f" {exists_marker.center(col_widths['Exists'])} " + "|"
            table.append(data_row)
            binary_name_displayed = True
        table.append(separator)  # Add a separator after each binary's files for clarity

    return "\n".join(table)




def github_releases():
    pass


def install_binaries():
    pass


def check_binaries_running():
    pass


def compare_versions():
    pass


def update_version_file():
    pass


def final_checks():
    pass


if __name__ == "__main__":
    print(binaries_to_table(is_binary_installed()))
