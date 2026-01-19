#!/bin/bash
# launch_direct.sh - Upload and execute direct boot deployment

TARGET="aimeat@192.168.6.97"
DEPLOY_DIR="/tmp/anvil_deploy"

echo ">> PROVISIONING REMOTE TARGET: $TARGET"
ssh $TARGET "mkdir -p $DEPLOY_DIR"

echo ">> UPLOADING KERNEL & INITRD..."
# Using paths from build/isolinux
scp build/isolinux/vmlinuz $TARGET:$DEPLOY_DIR/vmlinuz
# If initrd exists, upload it. 
if [ -f build/isolinux/initramfs.img ]; then
    scp build/isolinux/initramfs.img $TARGET:$DEPLOY_DIR/initrd
else
    echo "!! WARNING: initramfs.img not found in build/isolinux/"
fi

echo ">> UPLOADING SPAWN SCRIPT..."
scp artifacts/spawn_direct.sh $TARGET:$DEPLOY_DIR/
ssh $TARGET "chmod +x $DEPLOY_DIR/spawn_direct.sh"

echo ">> EXECUTING DEPLOYMENT..."
ssh -t $TARGET "sudo $DEPLOY_DIR/spawn_direct.sh"
