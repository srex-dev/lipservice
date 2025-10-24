#!/usr/bin/env python3
"""
Release script for LipService Python SDK.

This script helps manage versioning and publishing to PyPI.
"""

import os
import re
import subprocess
import sys
from pathlib import Path


def get_current_version():
    """Get current version from pyproject.toml."""
    pyproject_path = Path("sdk/python/pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    
    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        raise ValueError("Version not found in pyproject.toml")
    
    return match.group(1)


def update_version(new_version):
    """Update version in pyproject.toml and __init__.py."""
    # Update pyproject.toml
    pyproject_path = Path("sdk/python/pyproject.toml")
    content = pyproject_path.read_text()
    content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)
    pyproject_path.write_text(content)
    
    # Update __init__.py
    init_path = Path("sdk/python/lipservice/__init__.py")
    content = init_path.read_text()
    content = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', content)
    init_path.write_text(content)
    
    print(f"✅ Updated version to {new_version}")


def build_package():
    """Build the Python package."""
    print("🔨 Building package...")
    
    # Change to SDK directory
    os.chdir("sdk/python")
    
    try:
        # Clean previous builds
        subprocess.run(["rm", "-rf", "dist", "build", "*.egg-info"], check=False)
        
        # Build package
        subprocess.run([sys.executable, "-m", "build"], check=True)
        
        print("✅ Package built successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)
    finally:
        # Return to root directory
        os.chdir("../..")


def check_package():
    """Check the built package."""
    print("🔍 Checking package...")
    
    try:
        subprocess.run([sys.executable, "-m", "twine", "check", "sdk/python/dist/*"], check=True)
        print("✅ Package check passed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Package check failed: {e}")
        sys.exit(1)


def create_git_tag(version):
    """Create git tag for the release."""
    tag_name = f"sdk-python-v{version}"
    
    print(f"🏷️ Creating git tag: {tag_name}")
    
    try:
        # Add changes
        subprocess.run(["git", "add", "sdk/python/pyproject.toml", "sdk/python/lipservice/__init__.py"], check=True)
        
        # Commit changes
        subprocess.run(["git", "commit", "-m", f"Release Python SDK v{version}"], check=True)
        
        # Create tag
        subprocess.run(["git", "tag", "-a", tag_name, "-m", f"Release Python SDK v{version}"], check=True)
        
        print(f"✅ Git tag {tag_name} created")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operations failed: {e}")
        sys.exit(1)


def push_to_github():
    """Push changes and tags to GitHub."""
    print("🚀 Pushing to GitHub...")
    
    try:
        subprocess.run(["git", "push", "origin", "main"], check=True)
        subprocess.run(["git", "push", "origin", "--tags"], check=True)
        
        print("✅ Pushed to GitHub successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Push failed: {e}")
        sys.exit(1)


def main():
    """Main release process."""
    if len(sys.argv) != 2:
        print("Usage: python release.py <version>")
        print("Example: python release.py 0.2.0")
        sys.exit(1)
    
    new_version = sys.argv[1]
    current_version = get_current_version()
    
    print(f"🎙️ LipService Python SDK Release")
    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")
    print()
    
    # Confirm release
    confirm = input("Continue with release? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ Release cancelled")
        sys.exit(0)
    
    try:
        # Update version
        update_version(new_version)
        
        # Build package
        build_package()
        
        # Check package
        check_package()
        
        # Create git tag
        create_git_tag(new_version)
        
        # Push to GitHub
        push_to_github()
        
        print()
        print("🎉 Release completed successfully!")
        print()
        print("Next steps:")
        print("1. GitHub Actions will automatically publish to PyPI")
        print("2. Monitor the workflow at: https://github.com/srex-dev/lipservice/actions")
        print("3. Verify the package at: https://pypi.org/project/lipservice-sdk/")
        print()
        print(f"📦 Package will be available as: pip install lipservice-sdk=={new_version}")
        
    except Exception as e:
        print(f"❌ Release failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
