mkdir -p iso/boot/grub;cp kernel.bin iso/boot/;echo \"menuentry \\"Anvil\\"{multiboot2 /boot/kernel.bin;boot}\" > iso/boot/grub/grub.cfg;grub-mkrescue -o anvil.iso iso
