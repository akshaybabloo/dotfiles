"""
Installs third party binaries and keeps track of their versions.
"""

from dataclasses import dataclass
from typing import Tuple, List


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
    sha: SHAInfo | None
    file_names: List[str]
    description: str = ""

    def __post_init__(self):
        # Validate name is not empty
        if not self.name:
            raise ValueError("Name cannot be empty")

        # Validate URL format (this is a simplistic check; consider using regex for real URL validation)
        if not self.url.startswith("http://") and not self.url.startswith("https://"):
            raise ValueError("URL must start with 'http://' or 'https://'")

        # Validate that file_names is a list with at least one entry
        if not self.file_names or not isinstance(self.file_names, list):
            raise ValueError("file_names must be a non-empty list")


binaries: Tuple[Binaries, ...] = (
    Binaries(
        name="rclone",
        url="",
        sha=None,
        file_names=[],
    ),
    Binaries(
        name="Fs CLI",
        url="",
        sha=None,
        file_names=[],
    ),
    Binaries(
        name="7-Zip CLI",
        url="",
        sha=None,
        file_names=["7zzs"],
    ),
    Binaries(
        name="caddy",
        url="",
        sha=None,
        file_names=[],
    ),
    Binaries(
        name="WebP",
        url="",
        sha=None,
        file_names=["cwebp", "gif2webp"],
    ),
    Binaries(
        name="d2",
        url="",
        sha=None,
        file_names=[],
    ),
    Binaries(
        name="ffmpeg",
        url="",
        sha=None,
        file_names=["ffmpeg", "ffprobe"],
    ),
    Binaries(
        name="Git Alias",
        url="",
        sha=None,
        file_names=["git-alias"],
    ),
    Binaries(
        name="Hugo",
        url="",
        sha=None,
        file_names=["hugo"],
    ),
    Binaries(
        name="Just",
        url="",
        sha=None,
        file_names=["just"],
    ),
    Binaries(
        name="Mage",
        url="",
        sha=None,
        file_names=["mage"],
    ),
    Binaries(
        name="Oh My Posh",
        url="",
        sha=None,
        file_names=["oh-my-posh", "oh-my-posh.json", "themes/"],
    ),
    Binaries(
        name="Typst",
        url="",
        sha=None,
        file_names=["typst"],
    ),
    Binaries(
        name="DNode",
        url="",
        sha=None,
        file_names=["dnode"],
    ),
    Binaries(
        name="",
        url="",
        sha=None,
        file_names=[],
    ),
    Binaries(
        name="",
        url="",
        sha=None,
        file_names=[],
    ),
    Binaries(
        name="",
        url="",
        sha=None,
        file_names=[],
    ),
)


def github_releases():
    pass


def install_binaries():
    pass


def check_binaries_running():
    pass


def is_binary_installed():
    pass


def compare_versions():
    pass


def update_version_file():
    pass


def final_checks():
    pass


if __name__ == "__main__":
    pass
