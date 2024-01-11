#!/usr/bin/env python3

"""
Your module docstring here.
"""

import os
import shutil
import subprocess

MNT = "/tmp/maloneyos"
SWAPSIZE = 4
RESERVE = 1
DISK = open("/tmp/selected-disk", encoding="utf-8").read().strip()
USERNAME = open("/tmp/username", encoding="utf-8").read().strip()
PASSWORD = open("/tmp/password", encoding="utf-8").read().strip()

def cleanup():
    """
    Cleans up the system by removing existing boot entries, unmounting file systems,
    exporting active zpools, removing directories, and ensuring disk erasure.

    This function performs the following steps:
    1. Checks if the boot menu entry already exists and removes it if found.
    2. Creates the MNT directory if it does not exist.
    3. Unmounts various file systems.
    4. Exports active zpools.
    5. Clears the label of the zroot zpool.
    6. Removes the MNT directory and recreates it.
    7. Ensures the disk has been properly erased using wipefs.

    Note: The constants MNT and DISK are assumed to be defined elsewhere.

    """
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

def filesystem():
    """
    Creates and mounts filesystems.
    """
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

def install():
    """
    Extracts the system and makes other customizations.
    """
    # Extract the image
    subprocess.run(["unsquashfs", "-f", "-d", "/tmp/maloneyos", "/dev/loop0"])

    # Mounts for various OS commands to work
    subprocess.run(["mount", "-t", "devtmpfs", "none", os.path.join(MNT, "dev")])
    subprocess.run(["mount", "-t", "proc", "none", os.path.join(MNT, "proc")])
    subprocess.run(["mount", "-t", "sysfs", "none", os.path.join(MNT, "sys")])
    subprocess.run(["mount", "-t", "efivarfs", "none", os.path.join(MNT, "sys/firmware/efi/efivars")])

    # Copy files to the new system
    shutil.copy2("/etc/hostid", os.path.join(MNT, "etc/hostid"))

    # Copy vmlinuz needed for mkinitcpio to the installed system
    shutil.copy2("/run/archiso/bootmnt/arch/boot/x86_64/vmlinuz-linux-lts", os.path.join(MNT, "boot/"))

    # Copy microcode updates to the installed system
    shutil.copy2("/run/archiso/bootmnt/arch/boot/amd-ucode.img", os.path.join(MNT, "boot/"))
    shutil.copy2("/run/archiso/bootmnt/arch/boot/intel-ucode.img", os.path.join(MNT, "boot/"))

    # Generate proper preset for the installed system
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

    # Hardcode the timezone to UTC
    with open(os.path.join(MNT, "etc/locale.conf"), "w") as f:
        f.write("LANG=en_US.UTF-8\n")
        f.write("LC_COLLATE=C\n")

    with open(os.path.join(MNT, "etc/locale.gen"), "w") as f:
        f.write("en_US.UTF-8 UTF-8\n")
        f.write("C.UTF-8 UTF-8\n")

    subprocess.run(["arch-chroot", MNT, "locale-gen"])

    with open(os.path.join(MNT, "etc/timezone"), "w") as f:
        f.write("UTC\n")

    subprocess.run(["arch-chroot", MNT, "ln", "-sf", "/usr/share/zoneinfo/UTC", "/etc/localtime"])
    subprocess.run(["arch-chroot", MNT, "hwclock", "--systohc", "--utc"])

def user():
    """
    Creates the users and groups.
    """
    # Set root password
    subprocess.run(["arch-chroot", MNT, "echo", f"root:{PASSWORD}", "|", "chpasswd"])

    # Add user and set password
    subprocess.run(["arch-chroot", MNT, "useradd", "-m", "-g", "users", "-G", "wheel", USERNAME])
    subprocess.run(["arch-chroot", MNT, "echo", f"{USERNAME}:{PASSWORD}", "|", "chpasswd"])

    # Enable sudo for the wheel group
    subprocess.run(["arch-chroot", MNT, "sed", "-i", "/%wheel ALL=(ALL) ALL/s/^# //", "/etc/sudoers"])


def bootloader():
    """
    Setup and install the bootloader.
    """
    # Install systemd-boot
    subprocess.run(["arch-chroot", MNT, "bootctl", "install"])

    # Configure systemd-boot for MaloneyOS
    with open(os.path.join(MNT, "boot/loader/loader.conf"), "w") as f:
        f.write("default MaloneyOS.conf\n")
        f.write("timeout 0\n")

    # Create the systemd-boot entry
    with open(os.path.join(MNT, "boot/loader/entries/MaloneyOS.conf"), "w") as f:
        f.write("title MaloneyOS\n")
        f.write("linux /vmlinuz-linux-lts\n")
        f.write("initrd /amd-ucode.img\n")
        f.write("initrd /intel-ucode.img\n")
        f.write("initrd /initramfs-linux-lts.img\n")
        f.write("options zfs=zroot/ROOT/arch rw\n")

def services():
    """
    Starts services.
    """
    # Enable zfs-import-scan service
    subprocess.run(["arch-chroot", MNT, "systemctl", "enable", "zfs-import-scan"])

    # Set keyboard layout
    subprocess.run(["arch-chroot", MNT, "localectl", "set-keymap", "--no-convert", "us"])

    # Enable services
    subprocess.run(["arch-chroot", MNT, "systemctl", "enable", "NetworkManager"])
    subprocess.run(["arch-chroot", MNT, "systemctl", "enable", "sshd"])
    subprocess.run(["arch-chroot", MNT, "systemctl", "enable", "dhcpd4"])

def unmount():
    """
    Umounts filesystems for cleanup
    """
    subprocess.run(["umount", os.path.join(MNT, "dev")])
    subprocess.run(["umount", os.path.join(MNT, "proc")])
    subprocess.run(["umount", os.path.join(MNT, "sys/firmware/efi/efivars")])
    subprocess.run(["umount", os.path.join(MNT, "sys")])
    subprocess.run(["umount", os.path.join(MNT, "efi")])
    subprocess.run(["reboot"])

cleanup()
filesystem()
install()
user()
bootloader()
services()
unmount()
# Installation Complete