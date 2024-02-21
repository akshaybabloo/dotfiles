"""
Installs third party binaries and keeps track of their versions.
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

HOME_BIN = Path.home().joinpath("bin")


@dataclass
class VersionCommand:
    args: List[str]
    regex_version: str = ""

    def __post_init__(self):
        if not self.regex_version:
            raise ValueError("Command cannot be empty")
        if not self.args:
            raise ValueError("Args cannot be empty")


@dataclass
class Files:
    name: str
    exists: bool = False
    version: str = None
    version_command: Optional[VersionCommand] = None

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
            raise ValueError(f"sha_type must be one of 'SHA-1', 'SHA-256', 'SHA-512', not {self.type}")


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
        files=[
            Files(
                name="fs_rs",
                version_command=VersionCommand(args=["--version"], regex_version=r"\d+\.\d+\.\d+"),
            )
        ],
    ),
    Binaries(
        name="7-Zip CLI",
        url="https://",
        sha=None,
        files=[
            Files(
                name="7zzs",
                version_command=VersionCommand(args=[""], regex_version=r"\d+\.\d+"),
            )
        ],
    ),
    Binaries(
        name="caddy",
        url="https://",
        sha=None,
        files=[
            Files(
                name="caddy",
                version_command=VersionCommand(args=["version"], regex_version=r"v\d+\.\d+\.\d+"),
            )
        ],
    ),
    Binaries(
        name="WebP",
        url="https://",
        sha=None,
        files=[
            Files(
                name="cwebp",
                version_command=VersionCommand(args=["-version"], regex_version=r"\d+\.\d+\.\d+"),
            ),
            Files(
                name="gif2webp",
                version_command=VersionCommand(args=["-version"], regex_version=r"\d+\.\d+\.\d+"),
            ),
        ],
    ),
    Binaries(
        name="d2",
        url="https://",
        sha=None,
        files=[
            Files(
                name="d2",
                version_command=VersionCommand(args=["--version"], regex_version=r"v\d+\.\d+\.\d+"),
            )
        ],
    ),
    Binaries(
        name="ffmpeg",
        url="https://",
        sha=None,
        files=[
            Files(
                name="ffmpeg",
                version_command=VersionCommand(args=["-version"], regex_version=r"\d+\.\d+(?:\.\d+)?-static"),
            ),
            Files(
                name="ffprobe",
                version_command=VersionCommand(args=["-version"], regex_version=r"\d+\.\d+(?:\.\d+)?-static"),
            ),
        ],
    ),
    Binaries(
        name="Git Alias",
        url="https://",
        sha=None,
        files=[
            Files(
                name="git-alias",
                version_command=VersionCommand(args=["--version"], regex_version=r"\d+\.\d+\.\d+"),
            )
        ],
    ),
    Binaries(
        name="Hugo",
        url="https://",
        sha=None,
        files=[
            Files(
                name="hugo",
                version_command=VersionCommand(args=["version"], regex_version=r"v\d+\.\d+\.\d+"),
            )
        ],
    ),
    Binaries(
        name="Just",
        url="https://",
        sha=None,
        files=[
            Files(
                name="just",
                version_command=VersionCommand(args=["--version"], regex_version=r"\d+\.\d+\.\d+"),
            )
        ],
    ),
    Binaries(
        name="Mage",
        url="https://",
        sha=None,
        files=[
            Files(
                name="mage",
                version_command=VersionCommand(args=["-version"], regex_version=r"\d+\.\d+\.\d+"),
            )
        ],
    ),
    Binaries(
        name="Oh My Posh",
        url="https://",
        sha=None,
        files=[
            Files(
                name="oh-my-posh",
                version_command=VersionCommand(args=["--version"], regex_version=r"\d+\.\d+\.\d+"),
            ),
            Files(name="oh-my-posh.json"),
            Files(name="themes/"),
        ],
    ),
    Binaries(
        name="Typst",
        url="https://",
        sha=None,
        files=[
            Files(
                name="typst",
                version_command=VersionCommand(args=["--version"], regex_version=r"\d+\.\d+\.\d+"),
            )
        ],
    ),
    Binaries(
        name="DNode",
        url="https://",
        sha=None,
        files=[
            Files(
                name="dnode",
                version_command=VersionCommand(args=["--version"], regex_version=r"\d+\.\d+\.\d+"),
            )
        ],
    ),
]


def is_binary_installed() -> List[Binaries]:
    """
    Check if the binaries are installed in the home bin directory.

    :return: List of Binaries objects with the `exists` attribute updated
    """
    for binary in binaries:
        for file in binary.files:
            path = HOME_BIN.joinpath(file.name)
            if path.exists():
                file.exists = True
                if file.version_command:
                    command = [path]
                    if file.version_command.args[0] != "":
                        command.append(*file.version_command.args)
                    call = subprocess.run(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    version = call.stdout
                    match = re.search(rf"{file.version_command.regex_version}", version)
                    if match and not path.is_dir():
                        file.version = match.group(0)
                if path.is_dir() or path.suffix == ".json":
                    file.version = ""
    return binaries


def binaries_to_table(bin_files: List[Binaries]) -> str:
    headers = ["Binary Name", "File Name", "Version", "Exists"]
    col_widths = {
        "Binary Name": max(max((len(b.name) for b in bin_files), default=0), len(headers[0])),
        "File Name": max(
            max((len(f.name) for b in bin_files for f in b.files), default=0),
            len(headers[1]),
        ),
        "Version": max(
            max((len(str(f.version)) for b in bin_files for f in b.files), default=0),
            len(headers[2]),
        ),
        "Exists": len("Exists") + 2,  # Plus 2 for padding around [x] or [ ]
    }

    separator = "+" + "+".join(["-" * (col_widths[header] + 2) for header in headers]) + "+"
    header_row = "|" + "|".join([f" {header.center(col_widths[header])} " for header in headers]) + "|"
    table = [separator, header_row, separator]

    for binary in bin_files:
        binary_name_displayed = False
        for file in binary.files:
            binary_name = binary.name if not binary_name_displayed else ""
            exists_marker = "[x]" if file.exists else "[ ]"
            data_row = (
                "|"
                + f" {binary_name.ljust(col_widths['Binary Name'])} "
                + "|"
                + f" {file.name.ljust(col_widths['File Name'])} "
                + "|"
                + f" {str(file.version).ljust(col_widths['Version'])} "
                + "|"
                + f" {exists_marker.center(col_widths['Exists'])} "
                + "|"
            )
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
