#!/usr/bin/env python3
'''
Script to customize and make all prepartions before building.
'''
import os
import shutil
import subprocess

# Define variables
WORKDIR="/tmp/maloneyos"
ISO=f"{WORKDIR}/archiso-tmp"
RELENG=f"{WORKDIR}/archlive"

# Set the kernel version to be used in functions
KERNEL = "linux-lts"

def config():
    '''
    Copy configuration we will modify to make our customizations.
    '''
    # Copy the releng configuration
    shutil.copytree('/usr/share/archiso/configs/releng/', RELENG, symlinks=True)

def lts():
    '''
    Function to add OpenZFS package and repo.
    '''
    # Add linux-lts to packages.x86_64
    with open(os.path.join(RELENG, "packages.x86_64"), "a", encoding="utf-8") as f:
        f.write("linux-lts\n")

    # Remove line with the exact match of "linux" from packages.x86_64
    with open(os.path.join(RELENG, "packages.x86_64"), "r+") as f:
        lines = f.readlines()
    f.seek(0)
    for line in lines:
      if "linux" in line and line.strip() == "linux":
        continue
      f.write(line)
    f.truncate()

  
   # Remove packages that pull in linux from packages.x86_64
    with open(os.path.join(RELENG, "packages.x86_64"), "r+") as f:
        lines = f.readlines()
        f.seek(0)
        for line in lines:
            if not line.startswith(("broadcom-wl", "b43-fwcutter")):
            f.write(line)
        f.truncate()

    # Replace linux with linux-lts in syslinux bootloader for BIOS boot
    syslinux_cfg_path = os.path.join(RELENG, "syslinux", "archiso_sys-linux.cfg")
    with open(syslinux_cfg_path, "r+", encoding="utf-8") as f:
        content = f.read()
        content = content.replace("vmlinuz-linux", f"vmlinuz-{KERNEL}")
        content = content.replace("initramfs-linux.img", f"initramfs-{KERNEL}.img")
        f.seek(0)
        f.write(content)
        f.truncate()

    # Replace linux with linux-lts in efiboot bootloader for UEFI boot
    efiboot_cfg_path = os.path.join(RELENG, "efiboot", "loader", "entries", "01-archiso-x86_64-linux.conf")
    with open(efiboot_cfg_path, "r+", encoding="utf-8") as f:
        content = f.read()
        content = content.replace("vmlinuz-linux", f"vmlinuz-{KERNEL}")
        content = content.replace("initramfs-linux.img", f"initramfs-{KERNEL}.img")
        f.seek(0)
        f.write(content)
        f.truncate()

    # Replace linux with linux-lts in grub bootloader for UEFI boot
    grub_cfg_path = os.path.join(RELENG, "syslinux", "archiso_sys-linux.cfg")
    with open(grub_cfg_path, "r+", encoding="utf-8") as f:
        mkinitcpio_preset_path = os.path.join(RELENG, "airootfs", "etc", "mkinitcpio.d", "linux.preset")
        new_preset_path = os.path.join(RELENG, "airootfs", "etc", "mkinitcpio.d", f"{KERNEL}.preset")
        os.rename(mkinitcpio_preset_path, new_preset_path)
    with open(new_preset_path, "r+", encoding="utf-8") as f:
        content = f.read()
        content = content.replace("vmlinuz-linux", f"vmlinuz-{KERNEL}")
        content = content.replace("initramfs-linux.img", f"initramfs-{KERNEL}.img")
    f.seek(0)
    f.write(content)
    f.truncate()

    # Linux LTS doesn't support swapfiles option
    systemd_mount_path = os.path.join(RELENG, "airootfs", "etc", "systemd", "system", "etc-pacman.d-gnupg.mount")
    with open(systemd_mount_path, "r+", encoding="utf8") as f:
        content = f.read()
        content = content.replace(",noswap", "")
        f.seek(0)
        f.write(content)
        f.truncate()

def zfs():
    '''
    Add package and setup repo for OpenZFS.
    '''
    # Add zfs-linux to packages.x86_64
    with open(os.path.join(RELENG, "packages.x86_64"), "a", encoding="utf-8") as f:
        f.write("zfs-dkms\n")
        f.write(f"{KERNEL}-headers\n")

    # Add archzfs repository to pacman.conf
    pacman_conf_path = os.path.join(RELENG, "pacman.conf")
    with open(pacman_conf_path, "a", encoding="utf-8") as f:
        f.write("\n[archzfs]\nServer = https://zxcvfdsa.com/archzfs/$repo/x86_64\n")
        f.write("SigLevel = Never\n")

def plasma():
    # Add plasma packages to packages.x86_64
    '''
    Add plasma and various related packages.
    '''
    packages = [
      "plasma-desktop",
      "plasma-wayland-session",
      "ark",
      "discover",
      "dolphin",
      "flatpak",
      "kate",
      "kdialog",
      "kjournald",
      "konsole",
      "kwallet5",
      "kwalletmanager",
      "kwallet-pam",
      "git",
      'networkmanager',
      'plasma-nm',
      'plasma-systemmonitor',
      "pyqt5",
      "spectacle",
      "wget",
    ]
    with open(os.path.join(RELENG, "packages.x86_64"), "a", encoding="utf-8") as f:
        for package in packages:
            f.write(f"{package}\n")

def sddm():
    '''
    Configure SDDM and autologin.
    '''
    # Define sddm.conf path
    sddm_conf_path = os.path.join(RELENG, "airootfs", "etc", "sddm.conf.d", "autologin.conf")

    # Add sddm to packages.x86_64
    with open(os.path.join(RELENG, "packages.x86_64"), "a", encoding="utf-8") as f:
        f.write("sddm\n")

    # Add sddm to display-manager.service
    display_manager_path = os.path.join(RELENG, "airootfs", "etc", "systemd", "system", "display-manager.service")
    os.symlink("/usr/lib/systemd/system/sddm.service", display_manager_path)

    # Add autologin to sddm.conf
    os.makedirs(os.path.dirname(sddm_conf_path), exist_ok=True)
    with open(sddm_conf_path, "w", encoding="utf-8") as f:
        f.write("[Autologin]\n")
        f.write("User=archie\n")
        f.write("Session=plasma\n")

def user():
    '''
    Setup livecd user and add to groups.
    '''
    # Define user files
    passwd_file = os.path.join(RELENG, "airootfs", "etc", "passwd")
    shadow_file = os.path.join(RELENG, "airootfs", "etc", "shadow")
    group_file = os.path.join(RELENG, "airootfs", "etc", "group")
    gshadow_file = os.path.join(RELENG, "airootfs", "etc", "gshadow")
    sudoers_dir = os.path.join(RELENG, "airootfs", "etc", "sudoers.d")

    # Add user to airootfs
    with open(passwd_file, "a", encoding="utf-8") as f:
        f.write("archie:x:1000:1000::/home/archie:/usr/bin/zsh\n")
    with open(shadow_file, "a", encoding="utf-8") as f:
        f.write("archie:$6$veQypn8kEQiN8Qjm$SrUpS4dGB7LUmSImYV8y1jJPRug2mJ8TghJCoHGgfXTrMBViRmEV0yaCFcgruX9.CI9gMNRK99SqrtNlmyU3G.:14871::::::\n")
    with open(group_file, "a", encoding="utf-8") as f:
        f.write("root:x:0:root\n")
        f.write("adm:x:4:archie\n")
        f.write("wheel:x:10:archie\n")
        f.write("uucp:x:14:archie\n")
        f.write("archie:x:1000:\n")
    with open(gshadow_file, "a", encoding="utf-8") as f:
        f.write("root:!*::root\n")
        f.write("archie:!*::\n")
    with open(os.path.join(RELENG, "profiledef.sh"), "r+", encoding="utf-8") as f:
        content = f.read()
        content = content.replace("shadow.*=.*0:0:400", '[\"/etc/gshadow\"]=\"0:0:0400\"')
        f.seek(0)
        f.write(content)
        f.truncate()
    with open(os.path.join(RELENG, "profiledef.sh"), "r+", encoding="utf-8") as f:
        content = f.read()
        content = content.replace('["/usr/local/bin/livecd-sound"]="0:0:755"', '["/usr/local/bin/livecd-sound"]="0:0:755"\n  ["/home/archie/Desktop/installer.desktop"]="0:0:755"')
        f.seek(0)
        f.write(content)
        f.truncate()

    # Add archie to sudoers
    os.makedirs(sudoers_dir, exist_ok=True)
    with open(os.path.join(sudoers_dir, "00_archie"), "w", encoding="utf-8") as f:
        f.write("archie ALL=(ALL) NOPASSWD: ALL\n")

def installer():
    '''
    Copy the installer to ISO dir so it will be on the image.
    '''
    # Clone the repository to ISO/maloneyOS
    subprocess.run(["git", "clone", "https://github.com/pkgdemon/maloneyos.git", f"{RELENG}/airootfs/maloneyos"], check=True)

def desktop_shortcut():
    '''
    Create desktop shortcut for the live system user.
    '''
    desktop_folder = os.path.join(RELENG, "airootfs", "home", "archie", "Desktop")
    installer_desktop = os.path.join(RELENG, "airootfs", "maloneyos", "installer", "installer.desktop")
    os.makedirs(desktop_folder, exist_ok=True)
    shutil.copy(installer_desktop, desktop_folder)
    subprocess.run(["chown", "-R", "1000:1000", desktop_folder], check=True)
    subprocess.run(["chmod", "+x", installer_desktop], check=True)

config()
lts()
zfs()
plasma()
sddm()
user()
installer()
desktop_shortcut()

# End-of-file (EOF)
