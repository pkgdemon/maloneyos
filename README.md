maloneyos
=========
MaloneyOS is a distinct Linux distribution crafted for personal use. Unlike typical distributions, MaloneyOS is tailored exclusively for my individual use, with a focus on my customizations and personal preferences.  

![Screenshot_20240117_201413](https://github.com/pkgdemon/maloneyos/assets/4109732/bd06c1f1-7779-43be-8cbf-5100822a2131)


## Key Features

- **ZFS on Root Installation:** One of the unique aspects of MaloneyOS is the utilization of ZFS as the default filesystem through a single pool installation. The inclusion of the `zfs-dkms` package, along with a long-term release kernel, aims to minimize potential breakages associated with ZFS being an external kernel module.

- **Streamlined Bootloader Configuration:** By opting for a single ZFS pool instead of `bpool/rpool`, the need for tools like `zsys` to prevent grub-related issues is eliminated. Additionally, the inclusion of ZFSbootmenu, when paired with zectl` accessible through the installation of from AUR, allows for easy management and display of boot environments.

- **Custom Installer:** MaloneyOS features a custom installer developed to provide a deeper level of customization over the ZFS layout in backend.py. This decision was motivated by the desire to learn PyQT5 and overcome challenges encountered with packaging Calamares from the AUR. The result is a distribution that reflects a commitment to both functionality and personal learning goals.

- **KDE Desktop Environment:** MaloneyOS adopts KDE as the default desktop environment, offering a visually appealing and user-friendly interface.

- **Flatpak Integration:** Flatpaks are enabled, and the Discover application is configured exclusively for flatpaks. This design choice separates system updates with boot environments from application updates, providing a more streamlined and efficient update process.

Explore the latest release ISO for AMD64 systems with UEFI by clicking [here](https://github.com/pkgdemon/maloneyos/releases).

## Requirements for building from source code

* archiso
* python3
* sddm
* networkmanager

## Generating the ISO

```
make release
```

## Cleanup after building

```
make clean
```

## Credentials

The password for the archie user if needed is livecd.
