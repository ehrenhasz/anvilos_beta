#!/bin/bash
TARGET_DIR="oss_sovereignty/bld_02_Musl_Libc"
BUILD_SCRIPT="anvil.build.sh"

# 1. ANALYZE: Check 'anvil.build.sh' to identify the source repository URL.
# Extract relevant section from anvil.build.sh (replace with actual logic)
MUSL_SECTION="$(grep -A 20 "bld_02_Musl_Libc" "$BUILD_SCRIPT" | grep -v "bld_02_Musl_Libc" )"
DOWNLOAD_URL="$(echo "$MUSL_SECTION" | grep "wget" | head -n 1 | awk '{print $2}' | tr -d '"')" # Extract wget URL
TARBALL_NAME="$(basename "$DOWNLOAD_URL")"

# Check if the target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Target directory '$TARGET_DIR' does not exist. Creating it."
    mkdir -p "$TARGET_DIR"
fi

# 2. CLONE/DOWNLOAD: If the source code is not present, download it.
if [ ! -f "$TARGET_DIR/$TARBALL_NAME" ]; then
    echo "Source code not found. Downloading from: $DOWNLOAD_URL"
    cd "$TARGET_DIR" || exit 1
    wget "$DOWNLOAD_URL"
    cd .. # Return to previous directory
else
    echo "Source code found in '$TARGET_DIR'."
fi

# 3. DISCONNECT: Find and disconnect the git repository (if it exists).
if [ -d "$TARGET_DIR/.git" ]; then
  echo "Found .git directory in $TARGET_DIR. Disconnecting..."
  cd "$TARGET_DIR" || exit 1
  git remote remove origin
  cd .. # Return to previous directory
  echo "Disconnected git repository in '$TARGET_DIR'."
else
  echo "No .git directory found in '$TARGET_DIR'."
fi

# 4. REPORT: Output the status of the repository.
cd "$TARGET_DIR" || exit 1
if git remote get-url origin >/dev/null 2>&1; then
    echo "ERROR: Remote 'origin' still exists."
else
    echo "SUCCESS: No remote 'origin' found."
fi
cd ..
