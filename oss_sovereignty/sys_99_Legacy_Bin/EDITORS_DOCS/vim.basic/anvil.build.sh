#!/bin/bash
set -e
# ANVIL BUILD: Vim (Static/Minimal)

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../../.." && pwd )"
SOURCE_DIR="$PROJECT_ROOT/oss_sovereignty/sys_99_Legacy_Bin/EDITORS_DOCS/vim.basic/source"
BUILD_DIR="$PROJECT_ROOT/oss_sovereignty/sys_99_Legacy_Bin/EDITORS_DOCS/vim.basic/build"
INSTALL_DIR="$PROJECT_ROOT/oss_sovereignty/sys_99_Legacy_Bin/EDITORS_DOCS/vim.basic/dist"

# Dependencies
NCURSES_DIR="$PROJECT_ROOT/oss_sovereignty/sys_03_Libraries/ncurses/dist"

mkdir -p "$BUILD_DIR" "$INSTALL_DIR"

echo ">> [ANVIL] Configuring Vim..."
cd "$SOURCE_DIR"

# Clean if needed
make distclean || true

# Configure for Static Musl with Local Ncurses
export CC="$PROJECT_ROOT/ext/toolchain/bin/x86_64-unknown-linux-musl-gcc"
export CFLAGS="-static -Os -I$NCURSES_DIR/include -I$NCURSES_DIR/include/ncurses"
export LDFLAGS="-static -L$NCURSES_DIR/lib"
export LIBS="-lncurses -ltinfo"

./configure \
    --prefix="$INSTALL_DIR" \
    --with-features=small \
    --disable-gui \
    --without-x \
    --disable-netbeans \
    --disable-pythoninterp \
    --disable-perlinterp \
    --disable-rubyinterp \
    --disable-luainterp \
    --disable-tclinterp \
    --enable-multibyte \
    --disable-nls \
    --disable-selinux \
    --disable-gpm \
    --disable-sysmouse \
    --with-tlib=ncurses

# Note: osdef.h conflicts handled by patching osdef.sh/osdef2.h.in externally

echo ">> [ANVIL] Building Vim..."
make -j$(nproc)

echo ">> [ANVIL] Installing Vim..."
make install

echo ">> [ANVIL] Build Complete: $INSTALL_DIR/bin/vim"