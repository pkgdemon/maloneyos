#!/bin/bash

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script requires root privileges. Please run with 'sudo'."
    exit 1
fi

# Function to check for path to make sure we are running in arch linux livecd
check_path() {
    if [ ! -d "/run/archiso/cowspace" ]; then
        echo "Error: This installer can only be run in the Arch Linux LiveCD environment."
        exit 1
    fi
}

check_path

MNT="/tmp/maloneyos"
SWAPSIZE=4
RESERVE=1

# Mounts for various OS commands to work
mount -t devtmpfs none "${MNT}"/dev
mount -t proc none "${MNT}"/proc
mount -t sysfs none "${MNT}"/sys
mount -t efivarfs none "${MNT}"/sys/firmware/efi/efivars

# Generate fstab
genfstab -t PARTUUID "${MNT}" \
| grep -v swap \
| sed "s|vfat.*rw|vfat rw,x-systemd.idle-timeout=1min,x-systemd.automount,noauto,nofail|" \
> "${MNT}"/etc/fstab
sed -i '/zroot/d' "${MNT}"/etc/fstab

# Copy files to new system
rsync -a /etc/hostid "${MNT}"/etc/hostid

# Sync vmlinuz needed for mkinitcpio
rsync -a /run/archiso/bootmnt/arch/boot/x86_64/ "${MNT}"/boot/

# Generate proper preset for installed system
rm "${MNT}"/etc/mkinitcpio.conf.d/archiso.conf
echo "# mkinitcpio preset file for the 'linux-lts' package

#ALL_config=\"/etc/mkinitcpio.conf\"
ALL_kver=\"/boot/vmlinuz-linux-lts\"
ALL_microcode=(/boot/*-ucode.img)

PRESETS=('default' 'fallback')

#default_config=\"/etc/mkinitcpio.conf\"
default_image=\"/boot/initramfs-linux-lts.img\"
#default_uki=\"/efi/EFI/Linux/arch-linux-lts.efi\"
#default_options=\"--splash /usr/share/systemd/bootctl/splash-arch.bmp\"

#fallback_config=\"/etc/mkinitcpio.conf\"
fallback_image=\"/boot/initramfs-linux-lts-fallback.img\"
#fallback_uki=\"/efi/EFI/Linux/arch-linux-lts-fallback.efi\"
fallback_options=\"-S autodetect\"" > "${MNT}"/etc/mkinitcpio.d/linux-lts.preset

# Hardcode the timezone for now
chroot "${MNT}" ln -sf /usr/share/zoneinfo/America/New_York /etc/localtime
chroot "${MNT}" hwclock --systohc

# Harcode the locale for now
chroot "${MNT}" echo "en_US.UTF-8 UTF-8" /etc/locale.gen
chroot "${MNT}" locale-gen
chroot "${MNT}" echo 'LANG=en_US.UTF-8' > /etc/locale.conf
chroot "${MNT}" echo 'KEYMAP=de_CH-latin1' > /etc/vconsole.conf

# Configure mkinitcpio
chroot "${MNT}" sed -i 's|filesystems|zfs filesystems|' /etc/mkinitcpio.conf