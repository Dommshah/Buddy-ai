#!/usr/bin/env python3
"""Buddy.ai Setup — vibrant autonomous assistant."""
import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_dir = Path(__file__).parent

    print("=== Buddy.ai v2.1 Setup ===\n")

    # Install dependencies
    print("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=project_dir, check=True)

    # Create .env if not exists
    env_file = project_dir / ".env"
    env_example = project_dir / ".env.example"
    if not env_file.exists() and env_example.exists():
        print("\nCreating .env from template...")
        print(f"  Copy: {env_example} -> {env_file}")
        print(f"  ** Edit {env_file} and add your GEMINI_API_KEY **")

    # Create data directory
    data_dir = project_dir / "data" / "memory"
    data_dir.mkdir(parents=True, exist_ok=True)

    print("\nSetup complete! Buddy.ai ready.")
    print(f"\nNext steps:")
    print(f"  1. Edit {env_file} and add your GEMINI_API_KEY")
    print(f"  2. Run: buddy              # vibrant interactive")
    print(f"  3. Run: buddy --tools      # 49 categorized tools")
    print(f"  4. Run: buddy --offline    # qwen2.5:3b offline")


if __name__ == "__main__":
    main()
