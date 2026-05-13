#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

import requests

def download_file(url: str, output_path: Path):
    """Download a file from a URL with streaming."""
    print(f"Downloading {url} -> {output_path}")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Download completed.")

def git_commit_and_push(file_path: str, message: str, branch: str):
    """Add, commit, and push the file to the given branch."""
    # Ensure we are on the target branch (create if it doesn't exist)
    subprocess.run(['git', 'checkout', branch], check=False)
    subprocess.run(['git', 'checkout', '-B', branch], check=True)  # creates or switches

    # Add and commit
    subprocess.run(['git', 'add', file_path], check=True)
    result = subprocess.run(['git', 'commit', '-m', message],
                            capture_output=True, text=True)
    if result.returncode != 0:
        if "nothing to commit" in result.stderr + result.stdout:
            print("No changes to commit – file already exists and is identical?")
            return
        raise subprocess.CalledProcessError(result.returncode, result.args,
                                            output=result.stdout, stderr=result.stderr)

    # Push (use the token that was set by actions/checkout)
    subprocess.run(['git', 'push', 'origin', branch], check=True)
    print(f"Pushed changes to branch '{branch}'.")

def main():
    parser = argparse.ArgumentParser(
        description="Download a file and commit+push it to the git repository"
    )
    parser.add_argument('--url', required=True, help="URL of the file to download")
    parser.add_argument('--output', default='./downloaded_file',
                        help="Path where to save the file (relative to repo root)")
    parser.add_argument('--commit-message', default='Add downloaded release file',
                        help="Commit message")
    parser.add_argument('--branch', default='main',
                        help="Branch to commit and push to")
    args = parser.parse_args()

    output_path = Path(args.output)
    download_file(args.url, output_path)
    git_commit_and_push(str(output_path), args.commit_message, args.branch)

if __name__ == '__main__':
    main()
