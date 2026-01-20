#!/bin/bash
set -e
# ANVIL BUILD: Ncurses (Static/Minimal)

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../.." && pwd )"
SOURCE_DIR="$PROJECT_ROOT/oss_sovereignty/sys_03_Libraries/ncurses/source"
BUILD_DIR="$PROJECT_ROOT/oss_sovereignty/sys_03_Libraries/ncurses/build"
INSTALL_DIR="$PROJECT_ROOT/oss_sovereignty/sys_03_Libraries/ncurses/dist"

mkdir -p "$BUILD_DIR" "$INSTALL_DIR"

echo ">> [ANVIL] Configuring Ncurses..."
cd "$SOURCE_DIR"

# Clean if needed
make distclean || true

# Configure for Static Musl
export CC="$PROJECT_ROOT/ext/toolchain/bin/x86_64-unknown-linux-musl-gcc"
export CFLAGS="-static -Os -fPIC"
export LDFLAGS="-static"

# We build outside source tree usually, but ncurses supports in-tree.
# Let's try in-tree for simplicity or check if we can do out-of-tree.
# In-tree is safer for some legacy autotools.

./configure \
    --prefix="$INSTALL_DIR" \
    --without-cxx \
    --without-ada \
    --without-progs \
    --without-tests \
    --without-manpages \
    --with-termlib \
    --enable-termcap \
    --with-fallbacks=linux,vt100,xterm \
    --disable-database \
    --disable-home-terminfo \
    --enable-static \
    --disable-shared

echo ">> [ANVIL] Building Ncurses..."
make -j$(nproc)

echo ">> [ANVIL] Installing Ncurses..."
make install

echo ">> [ANVIL] Build Complete: $INSTALL_DIR/lib/libncurses.a"
