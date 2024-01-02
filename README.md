# maloneyos

This project will generate Arch Linux media with my customizations.

* LTS Kernel
* OpenZFS
* KDE Plasma 5

#### Requirements

The following packages are required to generate media for Arch Linux

* archiso
* sddm

#### Usage

Generating the ISO:

```
make release
```

Cleanup after build:

```
make clean
```

The password for archie user is livecd.