#!/bin/bash
mkdir -p isodir/boot/grub
cp kernel.bin isodir/boot/kernel.bin
echo 'menuentry "Anvil OS" {multiboot2 /boot/kernel.bin; boot}' > isodir/boot/grub/grub.cfg
grub-mkrescue -o anvil.iso isodir
