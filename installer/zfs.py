#!/usr/bin/env python3

import os
import subprocess

MNT = "/tmp/maloneyos"
SWAPSIZE = 4
RESERVE = 1
DISK = open("/tmp/selected-disk").read().strip()

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
