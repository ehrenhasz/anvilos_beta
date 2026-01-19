#!/bin/bash
# spawn_direct.sh - Direct kernel boot for Sovereign OS (V2)

VM_NAME="SovereignOS_V2"
RAM=2048
VCPUS=2
DISK_PATH="/tmp/anvil_deploy/sovereign_v2.qcow2"
KERNEL="/tmp/anvil_deploy/vmlinuz"
INITRD="/tmp/anvil_deploy/initrd"

# Ensure disk exists or create a placeholder
if [ ! -f "$DISK_PATH" ]; then
    echo ">> Creating disk image..."
    qemu-img create -f qcow2 "$DISK_PATH" 10G
fi

virt-install \
    --name "$VM_NAME" \
    --ram "$RAM" \
    --vcpus "$VCPUS" \
    --disk path="$DISK_PATH",format=qcow2 \
    --import \
    --network network=default \
    --boot kernel="$KERNEL",initrd="$INITRD",kernel_args="console=ttyS0 quiet" \
    --graphics none \
    --serial pty \
    --console pty,target_type=serial \
    --os-variant fedora-unknown \
    --check all=off

