#!/bin/bash
# card_ker_002.sh - Build Linux Kernel V2

KERNEL_DIR="oss_sovereignty/sys_01_Linux_Kernel/source"
TARGET_BIN="isodir/boot/kernel.bin"

echo ">> [KERNEL] Starting Build Process..."

if [ ! -d "$KERNEL_DIR" ]; then
    echo ">> [KERNEL] Source directory not found: $KERNEL_DIR"
    exit 1
fi

cd "$KERNEL_DIR" || exit 1

# 1. Configure
echo ">> [KERNEL] Configuring (defconfig + kvm_guest)..."
make x86_64_defconfig
# Enable KVM guest support and other drivers
./scripts/config --enable CONFIG_KVM_GUEST
./scripts/config --enable CONFIG_VIRTIO_PCI
./scripts/config --enable CONFIG_VIRTIO_NET
./scripts/config --enable CONFIG_VIRTIO_BLK
./scripts/config --enable CONFIG_E1000E
./scripts/config --enable CONFIG_IGB
./scripts/config --enable CONFIG_IXGBE
./scripts/config --enable CONFIG_IWLWIFI
./scripts/config --enable CONFIG_IWLMVM
./scripts/config --enable CONFIG_DRM_I915
./scripts/config --enable CONFIG_NVME_CORE
./scripts/config --enable CONFIG_NVME_MULTIPATH
./scripts/config --enable CONFIG_USB_XHCI_HCD
./scripts/config --enable CONFIG_THUNDERBOLT

# 2. Build
echo ">> [KERNEL] Building (bzImage)..."
make -j$(nproc) bzImage

# 3. Install
echo ">> [KERNEL] Installing to $TARGET_BIN..."
if [ -f "arch/x86/boot/bzImage" ]; then
    cp arch/x86/boot/bzImage "../../$TARGET_BIN" # Adjust path relative to source
    echo ">> [KERNEL] Build Complete: $TARGET_BIN"
else
    echo ">> [KERNEL] Error: bzImage not found!"
    exit 1
fi
