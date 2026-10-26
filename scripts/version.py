#!/usr/bin/env python3
"""Version management script for ld-sdk-check."""

import argparse
import sys
from pathlib import Path

def get_current_version():
    """Get the current version from VERSION file."""
    version_file = Path("VERSION")
    if version_file.exists():
        return version_file.read_text().strip()
    return "1.0.0"

def set_version(version):
    """Set the version in VERSION file."""
    version_file = Path("VERSION")
    version_file.write_text(version + "\n")
    print(f"Version updated to: {version}")

def bump_version(part="patch"):
    """Bump version number (major, minor, or patch)."""
    current = get_current_version()
    try:
        major, minor, patch = map(int, current.split('.'))
    except ValueError:
        print(f"Error: Invalid version format '{current}'. Expected X.Y.Z")
        return

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    elif part == "patch":
        patch += 1
    else:
        print(f"Error: Invalid part '{part}'. Use major, minor, or patch")
        return

    new_version = f"{major}.{minor}.{patch}"
    set_version(new_version)

def main():
    parser = argparse.ArgumentParser(description="Manage version for ld-simple-check")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Get current version
    subparsers.add_parser("get", help="Get current version")

    # Set version
    set_parser = subparsers.add_parser("set", help="Set version")
    set_parser.add_argument("version", help="Version to set (e.g., 1.2.3)")

    # Bump version
    bump_parser = subparsers.add_parser("bump", help="Bump version")
    bump_parser.add_argument("part", choices=["major", "minor", "patch"],
                            default="patch", nargs="?",
                            help="Part to bump (default: patch)")

    args = parser.parse_args()

    if args.command == "get":
        print(get_current_version())
    elif args.command == "set":
        set_version(args.version)
    elif args.command == "bump":
        bump_version(args.part)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()