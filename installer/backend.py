#!/usr/bin/env python3

import os
import shutil
import subprocess

MNT = "/tmp/maloneyos"
SWAPSIZE = 4
RESERVE = 1
DISK = open("/tmp/selected-disk").read().strip()
USERNAME = open("/tmp/username").read().strip()
PASSWORD = open("/tmp/password").read().strip()

# Check if the boot menu entry already exists
entries = ["MaloneyOS"]
for entry in entries:
    existing_entry = subprocess.check_output(["efibootmgr"]).decode()
    if entry in existing_entry:
        # Remove the existing entries before creating a new one
        entry_number = existing_entry.split()[0].replace("Boot", "").replace("*", "")
        subprocess.run(["efibootmgr", "-Bb", entry_number])

# Make MNT directory if it does not exist
if not os.path.isdir(MNT):
    os.mkdir(MNT)

# Unmount file systems
subprocess.run(["umount", f"{MNT}/dev"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["umount", f"{MNT}/proc"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["umount", f"{MNT}/sys/firmware/efi/efivars"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["umount", f"{MNT}/sys"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["umount", f"{MNT}/efi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Export active zpools
subprocess.run(["zpool", "export", "-a"])
subprocess.run(["zpool", "labelclear", "zroot", "-f"], stderr=subprocess.DEVNULL)

# Remove MNT directory and recreate it
subprocess.run(["rm", "-rf", MNT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
os.mkdir(MNT)

# Ensure disk has been erased properly with wipefs
subprocess.run(["wipefs", "-aq", DISK])

# Generate hostid
subprocess.run(["zgenhostid"])

# Partition the disk
subprocess.run(["sgdisk", "--zap-all", DISK])
subprocess.run(["sgdisk", "-n1:1M:+512M", "-t1:EF00", DISK])
subprocess.run(["sgdisk", "-n2:0:0", "-t2:BF00", DISK])

# Create zroot
subprocess.run(["zpool", "create", "-f",
                "-o", "ashift=12",
                "-o", "autotrim=on",
                "-O", "acltype=posixacl",
                "-O", "compression=zstd",
                "-O", "dnodesize=auto",
                "-O", "normalization=formD",
                "-O", "relatime=on",
                "-O", "xattr=sa",
                "-m", "none", "zroot", f"{DISK}2"])

# Create datasets
subprocess.run(["zfs", "create", "-o", "mountpoint=none", "zroot/ROOT"])
subprocess.run(["zfs", "create", "-o", "mountpoint=/", "-o", "canmount=noauto", "zroot/ROOT/arch"])
subprocess.run(["zfs", "create", "-o", "mountpoint=/home", "zroot/home"])

# Test the pool by importing and exporting
subprocess.run(["zpool", "export", "zroot"])
subprocess.run(["zpool", "import", "-N", "-R", MNT, "zroot"])
subprocess.run(["zfs", "mount", "zroot/ROOT/arch"])
subprocess.run(["zfs", "mount", "zroot/home"])

# Create and mount the EFI partition
subprocess.run(["mkfs.vfat", "-F", "32", "-n", "EFI", f"{DISK}1"])
os.mkdir(f"{MNT}/efi")
subprocess.run(["mount", f"{DISK}1", f"{MNT}/efi"])

# Extract the image
subprocess.run(["unsquashfs", "-f", "-d", "/tmp/maloneyos", "/dev/loop0"])

# Mounts for various OS commands to work
subprocess.run(["mount", "-t", "devtmpfs", "none", os.path.join(MNT, "dev")])
subprocess.run(["mount", "-t", "proc", "none", os.path.join(MNT, "proc")])
subprocess.run(["mount", "-t", "sysfs", "none", os.path.join(MNT, "sys")])
subprocess.run(["mount", "-t", "efivarfs", "none", os.path.join(MNT, "sys/firmware/efi/efivars")])

# Generate fstab
subprocess.run(["genfstab", "-t", "PARTUUID", MNT], text=True, check=True, stdout=open(os.path.join(MNT, "etc/fstab"), "w"))
subprocess.run(["sed", "-i", "/zroot/d", os.path.join(MNT, "etc/fstab")])

# Copy files to new system
shutil.copy2("/etc/hostid", os.path.join(MNT, "etc/hostid"))

# Copy vmlinuz needed for mkinitcpio to installed system
shutil.copy2("/run/archiso/bootmnt/arch/boot/x86_64/vmlinuz-linux-lts", os.path.join(MNT, "boot/"))

# Copy microcode updates to installed system
shutil.copy2("/run/archiso/bootmnt/arch/boot/amd-ucode.img", os.path.join(MNT, "boot/"))
shutil.copy2("/run/archiso/bootmnt/arch/boot/intel-ucode.img", os.path.join(MNT, "boot/"))

# Generate proper preset for installed system
os.remove(os.path.join(MNT, "etc/mkinitcpio.conf.d/archiso.conf"))
with open(os.path.join(MNT, "etc/mkinitcpio.d/linux-lts.preset"), "w") as f:
    f.write("# mkinitcpio preset file for the 'linux-lts' package\n\n")
    f.write("#ALL_config=\"/etc/mkinitcpio.conf\"\n")
    f.write("ALL_kver=\"/boot/vmlinuz-linux-lts\"\n")
    f.write("ALL_microcode=(/boot/*-ucode.img)\n\n")
    f.write("PRESETS=('default' 'fallback')\n\n")
    f.write("#default_config=\"/etc/mkinitcpio.conf\"\n")
    f.write("default_image=\"/boot/initramfs-linux-lts.img\"\n")
    f.write("#default_uki=\"/efi/EFI/Linux/arch-linux-lts.efi\"\n")
    f.write("#default_options=\"--splash /usr/share/systemd/bootctl/splash-arch.bmp\"\n\n")
    f.write("#fallback_config=\"/etc/mkinitcpio.conf\"\n")
    f.write("fallback_image=\"/boot/initramfs-linux-lts-fallback.img\"\n")
    f.write("#fallback_uki=\"/efi/EFI/Linux/arch-linux-lts-fallback.efi\"\n")
    f.write("fallback_options=\"-S autodetect\"\n")

# Hardcode the timezone for now
subprocess.run(["chroot", MNT, "ln", "-sf", "/usr/share/zoneinfo/America/New_York", "/etc/localtime"])
subprocess.run(["chroot", MNT, "hwclock", "--systohc"])

# Harcode the locale for now
subprocess.run(["chroot", MNT, "echo", "en_US.UTF-8 UTF-8", ">>", "/etc/locale.gen"])
subprocess.run(["chroot", MNT, "locale-gen"])
subprocess.run(["chroot", MNT, "echo", "LANG=en_US.UTF-8", ">", "/etc/locale.conf"])
subprocess.run(["chroot", MNT, "echo", "KEYMAP=de_CH-latin1", ">", "/etc/vconsole.conf"])

# Configure mkinitcpio
subprocess.run(["chroot", MNT, "sed", "-i", "s|filesystems|zfs filesystems|", "/etc/mkinitcpio.conf"])
subprocess.run(["chroot", MNT, "sed", "-i", "s|fsck||", "/etc/mkinitcpio.conf"])

# Run mkinitcpio
subprocess.run(["chroot", "/tmp/maloneyos", "mkinitcpio", "-P"])

# Set a cachefile for ZFS
subprocess.run(["chroot", MNT, "zpool", "set", "cachefile=/etc/zfs/zpool.cache", "zroot"])

# Set the bootfs
subprocess.run(["chroot", MNT, "zpool", "set", f"bootfs=zroot/ROOT/arch", "zroot"])

# Enable all needed daemons
subprocess.run(["chroot", MNT, "systemctl", "enable", "zfs-import-cache", "zfs-import.target", "zfs-mount", "zfs-zed", "zfs.target"])

# Create EFI subfolder
subprocess.run(["chroot", MNT, "mkdir", "-p", "/efi/EFI/zbm"])

# Get the latest zfsbootmenu
subprocess.run(["wget", "https://get.zfsbootmenu.org/latest.EFI", "-O", f"{MNT}/efi/EFI/zbm/zfsbootmenu.EFI"])

# Add an entry to your boot menu
subprocess.run(["chroot", MNT, "efibootmgr", "--disk", DISK, "--part", "1", "--create", "--label", "ZFSBootMenu", "--loader", "\\EFI\\zbm\\zfsbootmenu.EFI", "--unicode", f"spl_hostid=$(hostid) zbm.timeout=3 zbm.prefer=zroot zbm.import_policy=hostid", "--verbose"])

# Set the kernel parameters
subprocess.run(["chroot", MNT, "zfs", "set", f"org.zfsbootmenu:commandline=noresume init_on_alloc=0 rw spl.spl_hostid=$(hostid)", "zroot/ROOT"])

# Remove user "archie" from chroot
subprocess.run(["chroot", "/tmp/maloneyos", "userdel", "archie"])
subprocess.run(["chroot", "/tmp/maloneyos", "rm", "-rf", "/home/archie"])

# Add user with specified username
subprocess.run(["chroot", "/tmp/maloneyos", "useradd", "-m", "-G", "wheel", "-s", "/usr/bin/zsh", USERNAME])

# Set PASSWORD for the user
subprocess.run(["chroot", "/tmp/maloneyos", "chpasswd"], input=f"{USERNAME}:{PASSWORD}\n", text=True)

# Remove sddm.conf autologin
subprocess.run(["chroot", "/tmp/maloneyos", "rm", "/etc/sddm.conf.d/autologin.conf"])

sudoers_dir = "/tmp/maloneyos/etc/sudoers.d"
os.remove(f"{sudoers_dir}/00_archie")

with open(f"{sudoers_dir}/00_{USERNAME}", "w") as sudoers_file:
    sudoers_file.write(f"{USERNAME} ALL=(ALL) ALL\n")
    sudoers_file.write(f"{USERNAME} ALL=(ALL) ALL\n")

# Remove installer from installed system
subprocess.run(["rm", "-rf", f"{MNT}/maloneyos"])

# Unmount file systems
subprocess.run(["umount", f"{MNT}/dev"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["umount", f"{MNT}/proc"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["umount", f"{MNT}/sys/firmware/efi/efivars"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["umount", f"{MNT}/sys"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["umount", f"{MNT}/efi"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Export active zpools
subprocess.run(["zpool", "export", "-a"])
