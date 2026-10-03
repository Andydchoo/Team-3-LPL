"""Interactive, local-only setup of an event's temporary AWS credential profile."""

import argparse
import configparser
import getpass
import os
import sys
from pathlib import Path


def save_profile(profile: str, values: dict[str, str], aws_directory: Path):
    if not profile or "\n" in profile or "\r" in profile or "]" in profile:
        raise ValueError("Choose a valid AWS profile name")
    expected = {"aws_access_key_id", "aws_secret_access_key", "aws_session_token"}
    if set(values) != expected or any(not v or "\n" in v or "\r" in v for v in values.values()):
        raise ValueError("All three temporary credential values are required")
    aws_directory.mkdir(parents=True, exist_ok=True)
    credentials_path = aws_directory / "credentials"
    credentials = configparser.ConfigParser(interpolation=None)
    if credentials_path.exists():
        credentials.read(credentials_path, encoding="utf-8")
    # Replace this profile's stale options; preserve every other profile.
    credentials[profile] = values
    with credentials_path.open("w", encoding="utf-8") as stream:
        credentials.write(stream)
    if os.name != "nt":
        credentials_path.chmod(0o600)

    config_path = aws_directory / "config"
    config = configparser.ConfigParser(interpolation=None)
    if config_path.exists():
        config.read(config_path, encoding="utf-8")
    section = "default" if profile == "default" else f"profile {profile}"
    if not config.has_section(section):
        config.add_section(section)
    config.set(section, "region", "us-east-1")
    with config_path.open("w", encoding="utf-8") as stream:
        config.write(stream)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="revenue-hackathon")
    args = parser.parse_args()
    if not sys.stdin.isatty():
        print("Run this command in an interactive local terminal so credential input stays hidden.")
        return 1
    print("Enter the three values from the event AWS portal. Input is hidden.")
    values = {
        "aws_access_key_id": getpass.getpass("AWS access key ID: ").strip(),
        "aws_secret_access_key": getpass.getpass("AWS secret access key: ").strip(),
        "aws_session_token": getpass.getpass("AWS session token: ").strip(),
    }
    save_profile(args.profile, values, Path.home() / ".aws")
    print(f"Saved local AWS profile '{args.profile}' with region us-east-1.")
    print("Credential values were not printed or written into the repository.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
