#!/usr/bin/env python3

"""
Backend script that will process information collected during the install wizard and install.
"""

import os
import shutil
import subprocess

MNT = "/tmp/maloneyos"
SWAPSIZE = 4
RESERVE = 1

# Use 'with' statement for file operations
with open("/tmp/selected-disk", encoding="utf-8") as disk_file:
    DISK = disk_file.read().strip()

with open("/tmp/username", encoding="utf-8") as username_file:
    USERNAME = username_file.read().strip()

with open("/tmp/password", encoding="utf-8") as password_file:
    PASSWORD = password_file.read().strip()

def get_iso_device():
    '''
    This function only runs if it needs to when bootmnt is not mounted.
    '''
    try:
        # Run the shell command
        command = "lsblk -f | awk '/ARCH/ && /iso/ && NF {getline; print $1}' | sed 's/[^a-zA-Z0-9]//g'"
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)

        # Return the cleaned device name with /dev/ prefix
        iso_device = result.stdout.strip()
        return f"/dev/{iso_device}"

    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        return None

def detect_media():
    '''
    This function will get iso device if bootmnt is not mounted.
    '''
    try:
        # Check if /run/archiso/bootmnt exists
        bootmnt_path = '/run/archiso/bootmnt'

        if os.path.exists(bootmnt_path):
            print(f"{bootmnt_path} already exists. Skipping operation.")
            return

        # Get the ISO device
        iso_device = get_iso_device()

        if iso_device:
            print(f"The ISO device is: {iso_device}")

            # Create /run/archiso/bootmnt directory
            os.makedirs(bootmnt_path, exist_ok=True)
            print(f"Created directory: {bootmnt_path}")

            # Mount the ISO device to /run/archiso/bootmnt
            subprocess.run(['mount', iso_device, bootmnt_path], check=True)
            print(f"Mounted {iso_device} to {bootmnt_path}")

            # Continue with the rest of your logic here

        else:
            print("Failed to retrieve ISO device.")
            return

    except FileNotFoundError as e:
        print(f"File not found error: {e}")
    except PermissionError as e:
        print(f"Permission error: {e}")

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
    # Make MNT directory if it does not exist
    if not os.path.isdir(MNT):
        os.mkdir(MNT)

    # Unmount file systems if they are mounted
    if os.path.ismount(f"{MNT}/dev"):
        subprocess.run(["umount", f"{MNT}/dev"], check=True)
    if os.path.ismount(f"{MNT}/proc"):
        subprocess.run(["umount", f"{MNT}/proc"], check=True)
    if os.path.ismount(f"{MNT}/sys/firmware/efi/efivars"):
        subprocess.run(["umount", f"{MNT}/sys/firmware/efi/efivars"], check=True)
    if os.path.ismount(f"{MNT}/sys"):
        subprocess.run(["umount", f"{MNT}/sys"], check=True)
    if os.path.ismount(f"{MNT}/efi"):
        subprocess.run(["umount", f"{MNT}/efi"], check=True)

    # Export active zpools
    subprocess.run(["zpool", "export", "-a"], check=True)

    # Check if zroot pool exists
    existing_pools = subprocess.check_output(["zpool", "list", "-H", "-o", "name"]).decode().splitlines()
    if "zroot" in existing_pools:
        subprocess.run(["zpool", "labelclear", "zroot", "-f"], check=True)

    # Remove MNT directory and recreate it
    if os.path.exists(MNT):
        subprocess.run(["rm", "-rf", MNT], check=True)
    os.mkdir(MNT)

    # Ensure disk has been erased properly with wipefs
    subprocess.run(["wipefs", "-aq", DISK], check=True)

def filesystem():
    """
    Creates and mounts filesystems.
    """
    # Generate hostid
    subprocess.run(["zgenhostid", "-f"], check=True)

    # Partition the disk
    subprocess.run(["sgdisk", "--zap-all", DISK], check=True)
    subprocess.run(["sgdisk", "-n1:1M:+512M", "-t1:EF00", DISK], check=True)
    subprocess.run(["sgdisk", "-n2:0:0", "-t2:BF00", DISK], check=True)

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
                    "-m", "none", "zroot", f"{DISK}2"], check=True)

    # Create datasets
    subprocess.run(["zfs", "create", "-o", "mountpoint=none", "zroot/ROOT"], check=True)
    subprocess.run(["zfs", "create", "-o", "mountpoint=/", "-o", "canmount=noauto", "zroot/ROOT/arch"], check=True)
    subprocess.run(["zfs", "create", "-o", "mountpoint=/home", "zroot/home"], check=True)

    # Test the pool by importing and exporting
    subprocess.run(["zpool", "export", "zroot"], check=True)
    subprocess.run(["zpool", "import", "-N", "-R", MNT, "zroot"], check=True)
    subprocess.run(["zfs", "mount", "zroot/ROOT/arch"], check=True)
    subprocess.run(["zfs", "mount", "zroot/home"], check=True)

    # Create and mount the EFI partition
    subprocess.run(["mkfs.vfat", "-F", "32", "-n", "EFI", f"{DISK}1"], check=True)
    os.mkdir(f"{MNT}/efi")
    subprocess.run(["mount", f"{DISK}1", f"{MNT}/efi"], check=True)

def install():
    """
    Extracts the system and makes other customizations.
    """
    # Extract the image
    subprocess.run(["unsquashfs", "-f", "-d", "/tmp/maloneyos", "/dev/loop0"], check=True)

    # Mounts for various OS commands to work
    subprocess.run(["mount", "-t", "devtmpfs", "none", os.path.join(MNT, "dev")], check=True)
    subprocess.run(["mount", "-t", "proc", "none", os.path.join(MNT, "proc")], check=True)
    subprocess.run(["mount", "-t", "sysfs", "none", os.path.join(MNT, "sys")], check=True)
    subprocess.run(["mount", "-t", "efivarfs", "none", os.path.join(MNT, "sys/firmware/efi/efivars")], check=True)

    # Copy files to the new system
    shutil.copy2("/etc/hostid", os.path.join(MNT, "etc/hostid"))

def locale():
    '''
    Function to set keyboard mapping, timezone related things.
    '''
    subprocess.run(["chroot", MNT, "ln", "-sf", "/usr/share/zoneinfo/America/New_York", "/etc/localtime"], check=True)
    subprocess.run(["chroot", MNT, "hwclock", "--systohc"], check=True)
    subprocess.run(["chroot", MNT, "echo", "en_US.UTF-8 UTF-8", ">>", "/etc/locale.gen"], check=True)
    subprocess.run(["chroot", MNT, "locale-gen"], check=True)
    subprocess.run(["chroot", MNT, "echo", "LANG=en_US.UTF-8", ">", "/etc/locale.conf"], check=True)
    subprocess.run(["chroot", MNT, "echo", "KEYMAP=de_CH-latin1", ">", "/etc/vconsole.conf"], check=True)

def mkinitcpio():
    '''
    Function to prepare for and gererate image using mkinitcpio.
    '''
    # Copy vmlinuz needed for mkinitcpio to the installed system
    shutil.copy2("/run/archiso/bootmnt/arch/boot/x86_64/vmlinuz-linux-lts", os.path.join(MNT, "boot/"))

    # Copy microcode updates to the installed system
    shutil.copy2("/run/archiso/bootmnt/arch/boot/amd-ucode.img", os.path.join(MNT, "boot/"))
    shutil.copy2("/run/archiso/bootmnt/arch/boot/intel-ucode.img", os.path.join(MNT, "boot/"))

    # Generate proper preset for the installed system
    os.remove(os.path.join(MNT, "etc/mkinitcpio.conf.d/archiso.conf"))
    with open(os.path.join(MNT, "etc/mkinitcpio.d/linux-lts.preset"), "w", encoding="utf-8") as f:
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

    # Configure mkinitcpio
    subprocess.run(["chroot", MNT, "sed", "-i", "s|filesystems fsck|zfs filesystems|", "/etc/mkinitcpio.conf"], check=True)

    # Run mkinitcpio
    subprocess.run(["chroot", "/tmp/maloneyos", "mkinitcpio", "-P"], check=True)

def user():
    """
    Creates the users and groups.
    """
    # Remove user "archie" from chroot
    subprocess.run(["chroot", MNT, "userdel", "archie"], check=True)
    subprocess.run(["chroot", MNT, "rm", "-rf", "/home/archie"], check=True)

    # Remove archie from sudoers
    sudoers_dir = "/tmp/maloneyos/etc/sudoers.d"
    os.remove(f"{sudoers_dir}/00_archie")

    # Add user
    subprocess.run(["chroot", MNT, "useradd", "-m", "-g", "users", "-G", "wheel", USERNAME], check=True)

    # Set PASSWORD for the user
    subprocess.run(["chroot", MNT, "chpasswd"], input=f"{USERNAME}:{PASSWORD}\n", text=True, check=True)

    # Remove sddm.conf autologin
    subprocess.run(["chroot", MNT, "rm", "/etc/sddm.conf.d/autologin.conf"], check=True)

    # Add user to sudoers.d
    with open(f"{sudoers_dir}/00_{USERNAME}", "w", encoding="utf-8") as sudoers_file:
        sudoers_file.write(f"{USERNAME} ALL=(ALL) ALL\n")

    # Remove installer from installed system
    subprocess.run(["rm", "-rf", f"{MNT}/maloneyos"], check=True)

def bootloader():
    """
    Setup and install the bootloader.
    """
    # Set a cachefile for ZFS
    subprocess.run(["chroot", MNT, "zpool", "set", "cachefile=/etc/zfs/zpool.cache", "zroot"], check=True)

    # Set the bootfs
    subprocess.run(["chroot", MNT, "zpool", "set", "bootfs=zroot/ROOT/arch", "zroot"], check=True)

    # Enable all needed daemons
    subprocess.run(["chroot", MNT, "systemctl", "enable", "zfs-import-cache", "zfs-import.target", "zfs-mount", "zfs-zed", "zfs.target"], check=True)

    # Create EFI subfolder
    subprocess.run(["chroot", MNT, "mkdir", "-p", "/efi/EFI/zbm"], check=True)

    # Move /zfsbootmenu.EFI to /efi/EFI/zbm/zfsbootmenu.EFI
    chroot_path = MNT
    source_path = os.path.join(chroot_path, "zfsbootmenu.EFI")
    destination_path = os.path.join(chroot_path, "efi", "EFI", "zbm", "zfsbootmenu.EFI")
    shutil.move(source_path, destination_path)

    # Add an entry to your boot menu
    subprocess.run(["chroot", MNT, "efibootmgr", "--disk", DISK, "--part", "1", "--create", "--label", "ZFSBootMenu", "--loader", "\\EFI\\zbm\\zfsbootmenu.EFI", "--unicode", "spl_hostid=$(hostid) zbm.timeout=3 zbm.prefer=zroot zbm.import_policy=hostid", "--verbose"], check=True)

    # Set the kernel parameters
    subprocess.run(["chroot", MNT, "zfs", "set", "org.zfsbootmenu:commandline=noresume init_on_alloc=0 rw spl.spl_hostid=$(hostid)", "zroot/ROOT"], check=True)

def services():
    """
    Starts services.
    """
    # Enable zfs services
    subprocess.run(["chroot", MNT, "systemctl", "enable", "zfs-import-cache", "zfs-import.target", "zfs-mount", "zfs-zed", "zfs.target"], check=True)

def unmount():
    """
    Umounts filesystems for cleanup
    """
    subprocess.run(["umount", os.path.join(MNT, "dev")], check=True)
    subprocess.run(["umount", os.path.join(MNT, "proc")], check=True)
    subprocess.run(["umount", os.path.join(MNT, "sys/firmware/efi/efivars")], check=True)
    subprocess.run(["umount", os.path.join(MNT, "sys")], check=True)
    subprocess.run(["umount", os.path.join(MNT, "efi")], check=True)

def export_pools():
    """
    Here we export all pools so system will boot cleanly.
    """
    subprocess.run(["zpool", "export", "-a"], check=True)

detect_media()
cleanup()
filesystem()
install()
locale()
mkinitcpio()
user()
bootloader()
services()
unmount()
export_pools()

# End-of-file (EOF)
