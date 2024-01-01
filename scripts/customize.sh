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

lts
zfs