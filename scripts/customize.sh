#!/bin/bash

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script requires root privileges. Please run with 'sudo'."
    exit 1
fi

# Source the build configuration file
source ../config/build.conf

# Set the kernel version to be used in functions
KERNEL=linux-lts

lts()
{
  # Add linux-lts to packages.x86_64
  sed -i '/linux-firmware-marvell/a linux-lts' ${RELENG}/packages.x86_64

  # Remove linux and packages that pull in linux from packages.x86_64
  sed -i '/^linux$/d' ${RELENG}/packages.x86_64
  sed -i '/broadcom-wl/d' ${RELENG}/packages.x86_64
  sed -i '/b43-fwcutter/d' ${RELENG}/packages.x86_64

  # Replace linux with linux-lts in syslinux bootloader for BIOS boot
  sed -i "s/vmlinuz-linux/vmlinuz-${KERNEL}/" ${RELENG}/syslinux/archiso_sys-linux.cfg
  sed -i "s/initramfs-linux.img/initramfs-${KERNEL}.img/" ${RELENG}/syslinux/archiso_sys-linux.cfg
  sed -i "s/vmlinuz-linux/vmlinuz-${KERNEL}/" ${RELENG}/syslinux/archiso_pxe-linux.cfg
  sed -i "s/initramfs-linux.img/initramfs-${KERNEL}.img/" ${RELENG}/syslinux/archiso_pxe-linux.cfg

  # Replace linux with linux-lts in efiboot bootloader for UEFI boot
  sed -i "s/vmlinuz-linux/vmlinuz-${KERNEL}/" ${RELENG}/efiboot/loader/entries/01-archiso-x86_64-linux.conf
  sed -i "s/initramfs-linux.img/initramfs-${KERNEL}.img/" ${RELENG}/efiboot/loader/entries/01-archiso-x86_64-linux.conf
  sed -i "s/vmlinuz-linux/vmlinuz-${KERNEL}/" ${RELENG}/efiboot/loader/entries/02-archiso-x86_64-speech-linux.conf
  sed -i "s/initramfs-linux.img/initramfs-${KERNEL}.img/" ${RELENG}/efiboot/loader/entries/02-archiso-x86_64-speech-linux.conf

  # Replace linux with linux-lts in grub bootloader for UEFI boot
  sed -i 's/vmlinuz-linux/vmlinuz-linux-lts/g' ${RELENG}/grub/grub.cfg
  sed -i 's/initramfs-linux.img/initramfs-linux-lts.img/g' ${RELENG}/grub/grub.cfg

  # Replace linux preset with linux-lts mkinitcpio preset  
  mv ${RELENG}/airootfs/etc/mkinitcpio.d/linux.preset ${RELENG}//airootfs/etc/mkinitcpio.d/${KERNEL}.preset
  sed -i "s/vmlinuz-linux/vmlinuz-${KERNEL}/" ${RELENG}/airootfs/etc/mkinitcpio.d/${KERNEL}.preset
  sed -i "s/initramfs-linux.img/initramfs-${KERNEL}.img/" ${RELENG}//airootfs/etc/mkinitcpio.d/${KERNEL}.preset

  # Linux LTS doesn't support swapfiles option
  sed -i 's/,noswap//' ${RELENG}/airootfs/etc/systemd/system/etc-pacman.d-gnupg.mount
}

zfs()
{
  # Add zfs-linux to packages.x86_64
  echo "zfs-dkms" >> ${RELENG}/packages.x86_64
  echo "${KERNEL}-headers" >> ${RELENG}/packages.x86_64
  
  # Add archzfs repository to pacman.conf
  echo -e "\n[archzfs]\nServer = https://zxcvfdsa.com/archzfs/\$repo/x86_64" >> ${RELENG}/pacman.conf
  echo "SigLevel = Never" >> ${RELENG}/pacman.conf
}

plasma() {
  # Add plasma packages to packages.x86_64
  local packages=(
    'plasma-desktop'
    'plasma-wayland-session'
    'ark'
    'dolphin'
    'falkon'
    'kate'
    'kdialog'
    'konsole'
    'spectacle'
  )

  for package in "${packages[@]}"; do
    echo "$package" >> "${RELENG}/packages.x86_64"
  done
}

sddm() 
{
  # Define sddm.conf path
  local sddm_conf="${RELENG}/airootfs/etc/sddm.conf.d/autologin.conf"

  # Add sddm to packages.x86_64
  echo 'sddm' >> "${RELENG}/packages.x86_64"
  
  # Add sddm to display-manager.service
  ln -s /usr/lib/systemd/system/sddm.service "${RELENG}/airootfs/etc/systemd/system/display-manager.service"
  
  # Add autologin to sddm.conf
  mkdir -p "${RELENG}/airootfs/etc/sddm.conf.d"
  echo '[Autologin]' >> $sddm_conf
  echo 'User=archie' >> $sddm_conf
  echo 'Session=plasma' >> $sddm_conf
}

user()
{
  # Define user files
  local passwd_file="${RELENG}/airootfs/etc/passwd"
  local shadow_file="${RELENG}/airootfs/etc/shadow"
  local group_file="${RELENG}/airootfs/etc/group"
  local gshadow_file="${RELENG}/airootfs/etc/gshadow"
  local sudoers_dir="${RELENG}/airootfs/etc/sudoers.d"

  # Add user to airootfs
  echo 'archie:x:1000:1000::/home/archie:/usr/bin/zsh' >> "$passwd_file"
  echo 'archie:$6$veQypn8kEQiN8Qjm$SrUpS4dGB7LUmSImYV8y1jJPRug2mJ8TghJCoHGgfXTrMBViRmEV0yaCFcgruX9.CI9gMNRK99SqrtNlmyU3G.:14871::::::' >> "$shadow_file"
  echo 'root:x:0:root' >> "$group_file"
  echo 'adm:x:4:archie' >> "$group_file"
  echo 'wheel:x:10:archie' >> "$group_file"
  echo 'uucp:x:14:archie' >> "$group_file"
  echo 'archie:x:1000:' >> "$group_file"
  echo 'root:!*::root' >> "$gshadow_file"
  echo 'archie:!*::' >> "$gshadow_file"
  sed -i '/shadow.*=.*0:0:400/a \ \ ["/etc/gshadow"]="0:0:0400"' "${RELENG}/profiledef.sh"

  # Add archie to sudoers
  mkdir -p "$sudoers_dir"
  echo 'archie ALL=(ALL) ALL' >> "$sudoers_dir/00_archie"
  echo 'archie ALL=(ALL) ALL' >> "$sudoers_dir/00_archie"
}

lts
zfs
plasma
sddm
user