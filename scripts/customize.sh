#!/bin/bash

source ../config/build.conf

KERNEL=linux-lts

lts()
{
  sed -i '/linux-firmware-marvell/a linux-lts' ${RELENG}/packages.x86_64
  sed -i '/^linux$/d' ${RELENG}/packages.x86_64
  sed -i '/broadcom-wl/d' ${RELENG}/packages.x86_64
  sed -i '/b43-fwcutter/d' ${RELENG}/packages.x86_64
  sed -i "s/vmlinuz-linux/vmlinuz-${KERNEL}/" ${RELENG}/syslinux/archiso_sys-linux.cfg
  sed -i "s/initramfs-linux.img/initramfs-${KERNEL}.img/" ${RELENG}/syslinux/archiso_sys-linux.cfg
  sed -i "s/vmlinuz-linux/vmlinuz-${KERNEL}/" ${RELENG}/syslinux/archiso_pxe-linux.cfg
  sed -i "s/initramfs-linux.img/initramfs-${KERNEL}.img/" ${RELENG}/syslinux/archiso_pxe-linux.cfg
  sed -i "s/vmlinuz-linux/vmlinuz-${KERNEL}/" ${RELENG}/efiboot/loader/entries/01-archiso-x86_64-linux.conf
  sed -i "s/initramfs-linux.img/initramfs-${KERNEL}.img/" ${RELENG}/efiboot/loader/entries/01-archiso-x86_64-linux.conf
  sed -i "s/vmlinuz-linux/vmlinuz-${KERNEL}/" ${RELENG}/efiboot/loader/entries/02-archiso-x86_64-speech-linux.conf
  sed -i "s/initramfs-linux.img/initramfs-${KERNEL}.img/" ${RELENG}/efiboot/loader/entries/02-archiso-x86_64-speech-linux.conf
  sed -i 's/vmlinuz-linux/vmlinuz-linux-lts/g' ${RELENG}/grub/grub.cfg
  sed -i 's/initramfs-linux.img/initramfs-linux-lts.img/g' ${RELENG}/grub/grub.cfg
  mv ${RELENG}/airootfs/etc/mkinitcpio.d/linux.preset ${RELENG}//airootfs/etc/mkinitcpio.d/${KERNEL}.preset
  sed -i "s/vmlinuz-linux/vmlinuz-${KERNEL}/" ${RELENG}/airootfs/etc/mkinitcpio.d/${KERNEL}.preset
  sed -i "s/initramfs-linux.img/initramfs-${KERNEL}.img/" ${RELENG}//airootfs/etc/mkinitcpio.d/${KERNEL}.preset
  sed -i 's/,noswap//' ${RELENG}/airootfs/etc/systemd/system/etc-pacman.d-gnupg.mount

}

zfs()
{
  echo "zfs-dkms" >> ${RELENG}/packages.x86_64
  echo "${KERNEL}-headers" >> ${RELENG}/packages.x86_64
  echo -e "\n[archzfs]\nServer = https://zxcvfdsa.com/archzfs/\$repo/x86_64" >> ${RELENG}/pacman.conf
  echo "SigLevel = Never" >> ${RELENG}/pacman.conf
}

plasma()
{
  echo 'plasma-desktop' >> ${RELENG}/packages.x86_64
  echo 'plasma-wayland-session' >> ${RELENG}/packages.x86_64
  echo 'sddm' >> ${RELENG}/packages.x86_64
  echo 'konsole' >> ${RELENG}/packages.x86_64
  ln -s /usr/lib/systemd/system/sddm.service ${RELENG}/airootfs/etc/systemd/system/display-manager.service
  mkdir ${RELENG}/airootfs/etc/sddm.conf.d
  echo '[Autologin]' >> ${RELENG}/airootfs/etc/sddm.conf.d/autologin.conf
  echo 'User=archie' >> ${RELENG}/airootfs/etc/sddm.conf.d/autologin.conf
  echo 'Session=plasma' >> ${RELENG}/airootfs/etc/sddm.conf.d/autologin.conf
}

user()
{
  echo 'archie:x:1000:1000::/home/archie:/usr/bin/zsh' >> ${RELENG}/airootfs/etc/passwd
  echo 'archie:$6$veQypn8kEQiN8Qjm$SrUpS4dGB7LUmSImYV8y1jJPRug2mJ8TghJCoHGgfXTrMBViRmEV0yaCFcgruX9.CI9gMNRK99SqrtNlmyU3G.:14871::::::' >> ${RELENG}/airootfs/etc/shadow
  echo 'root:x:0:root' >> ${RELENG}/airootfs/etc/group
  echo 'adm:x:4:archie' >> ${RELENG}/airootfs/etc/group
  echo 'wheel:x:10:archie' >> ${RELENG}/airootfs/etc/group
  echo 'uucp:x:14:archie' >> ${RELENG}/airootfs/etc/group
  echo 'archie:x:1000:' >> ${RELENG}/airootfs/etc/group
  echo 'root:!*::root' >> ${RELENG}/airootfs/etc/gshadow
  echo 'archie:!*::' >> ${RELENG}/airootfs/etc/gshadow
  sed -i '/shadow.*=.*0:0:400/a \ \ ["/etc/gshadow"]="0:0:0400"' ${RELENG}/profiledef.sh
}

lts
zfs
plasma
user