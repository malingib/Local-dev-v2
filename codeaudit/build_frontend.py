"""
Build the frontend and copy it to the codeaudit frontend/dist location.
Run this from the codeaudit directory.
"""
import subprocess
import sys
import shutil
from pathlib import Path

# This file lives in codeaudit/, app/ is a sibling
CODEAUDIT = Path(__file__).resolve().parent
APP_DIR = CODEAUDIT.parent / "app"
DIST = APP_DIR / "dist"
FRONTEND_DIST = CODEAUDIT / "frontend" / "dist"

def build():
    if not APP_DIR.exists():
        print(f"Error: app directory not found at {APP_DIR}")
        sys.exit(1)

    # Install dependencies
    print("Installing dependencies...")
    subprocess.run(["npm", "install"], cwd=str(APP_DIR), check=True)

    # Build
    print("Building frontend...")
    subprocess.run(["npm", "run", "build"], cwd=str(APP_DIR), check=True)

    # Copy to codeaudit/frontend/dist
    if FRONTEND_DIST.exists():
        shutil.rmtree(FRONTEND_DIST)
    shutil.copytree(DIST, FRONTEND_DIST)
    print(f"Built and copied to {FRONTEND_DIST}")

if __name__ == "__main__":
    build()
