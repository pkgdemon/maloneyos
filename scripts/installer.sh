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

# Check if the boot menu entry already exists
entries=("MaloneyOS")
for entry in "${entries[@]}"; do
    existing_entry=$(efibootmgr | grep "$entry")
    if [[ -n "$existing_entry" ]]; then
        # Remove the existing entries before creating a new one
        entry_number=$(echo "$existing_entry" | awk '{print $1}' | sed 's/Boot//' | sed 's/^00//' | tr -d '*')
        efibootmgr -Bb "$entry_number"
    fi
done

# Make MNT directory if it does not exist
if [ ! -d "${MNT}" ]; then
    mkdir "${MNT}"
fi

# Get a list of disk names excluding loop and sr0 devices
disk_names=$(lsblk -o NAME -n -p -r | grep -vE "loop|sr0|[0-9]")

# Create an array of menu items
menu_items=()
while read -r disk_name; do
    menu_items+=("$disk_name" "$disk_name")
done <<< "$disk_names"

# Use kdialog to present the menu
selected_disk=$(kdialog --menu "Select a disk:" "${menu_items[@]}" 2>/dev/null)

# Check if a disk is selected
if [ -z "$selected_disk" ] || [ "$selected_disk" == "cancel" ]; then
    kdialog --error "Error: No disk selected. Please choose a disk." 2>/dev/null
    selected_disk=""
    exit 1
fi

# Store the selected disk in the DISK variable
DISK="$selected_disk"

# Display the selected disk
kdialog --msgbox "You selected: $DISK" 2>/dev/null

# Unmount file  systems
umount "${MNT}"/dev >/dev/null 2>&1
umount "${MNT}"/proc >/dev/null 2>&1
umount "${MNT}"/sys/firmware/efi/efivars >/dev/null 2>&1
umount "${MNT}"/sys >/dev/null 2>&1
umount ${MNT}/efi >/dev/null 2>&1

# Export active zpools
zpool export -a
zpool labelclear zroot -f 2>/dev/null

# Remove MNT directory and recreate it
rm -rf "${MNT}" >/dev/null 2>&1
mkdir "${MNT}" >/dev/null 2>&1

# Ensure disk has been erased properly with wipefs
wipefs -aq "$DISK"

# Generate hostid
zgenhostid

# Partition the disk
sgdisk --zap-all $DISK
sgdisk -n1:1M:+512M -t1:EF00 $DISK
sgdisk -n2:0:0 -t2:BF00 $DISK

# Create zroot
zpool create -f \
 -o ashift=12 \
 -o autotrim=on \
 -O acltype=posixacl \
 -O compression=zstd \
 -O dnodesize=auto \
 -O normalization=formD \
 -O relatime=on \
 -O xattr=sa \
 -m none zroot "${DISK}"2

# Create datasets
zfs create -o mountpoint=none zroot/ROOT
zfs create -o mountpoint=/ -o canmount=noauto zroot/ROOT/arch
zfs create -o mountpoint=/home zroot/home

# Test the pool by importing and exporting
zpool export zroot
zpool import -N -R "${MNT}" zroot
zfs mount zroot/ROOT/arch
zfs mount zroot/home

# Create and mount the EFI partition
mkfs.vfat -F 32 -n EFI ${DISK}1
mkdir "${MNT}"/efi
mount "${DISK}"1 "${MNT}"/efi

# Use unsquashfs to extract the squashfs image to the ZFS root
unsquashfs -f -d "${MNT}" /dev/loop0

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
chroot "${MNT}" mkinitcpio -P

# Set a cachefile for ZFS
chroot "${MNT}" zpool set cachefile=/etc/zfs/zpool.cache zroot

# Set the bootfs
chroot "${MNT}" zpool set bootfs=zroot/ROOT/arch zroot

# Enable all needed daemons
chroot "${MNT}" systemctl enable zfs-import-cache zfs-import.target zfs-mount zfs-zed zfs.target

# Create EFI subfolder
chroot "${MNT}" mkdir -p /efi/EFI/zbm

# Get the latest zfsbootmenu
wget https://get.zfsbootmenu.org/latest.EFI -O "${MNT}"/efi/EFI/zbm/zfsbootmenu.EFI

# Add an entry to your boot menu
chroot "${MNT}" efibootmgr --disk "${DISK}" --part 1 --create --label "ZFSBootMenu" --loader '\EFI\zbm\zfsbootmenu.EFI' --unicode "spl_hostid=$(hostid) zbm.timeout=3 zbm.prefer=zroot zbm.import_policy=hostid" --verbose

# Set the kernel parameters
chroot "${MNT}" zfs set org.zfsbootmenu:commandline="noresume init_on_alloc=0 rw spl.spl_hostid=$(hostid)" zroot/ROOT

# Unmount file  systems
umount "${MNT}"/dev >/dev/null 2>&1
umount "${MNT}"/proc >/dev/null 2>&1
umount "${MNT}"/sys/firmware/efi/efivars >/dev/null 2>&1
umount "${MNT}"/sys >/dev/null 2>&1
umount "${MNT}"/efi >/dev/null 2>&1

# Export active zpools
zpool export -a