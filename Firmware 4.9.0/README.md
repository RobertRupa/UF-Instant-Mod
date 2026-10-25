# UF-Instant 4.9.0 mod

This is a small update for UF-INSTANT firmware **v4.9.0.2229-828.241128.1332**.

The idea is the same as the old mod: keep the original Ubiquiti firmware on one image, and use the second image for the custom version. This time the GPON serial number can be overridden without changing the stick's hardware partition.

# What was changed

- `omci_app` from firmware 4.9.0 has a MIPS hook that reads an optional serial number from `/var/config/gpon_sn_override`.
- The value must be **16 hexadecimal characters** (8 bytes), with an optional trailing newline. Invalid or missing values leave the default SN unchanged.
- The value is copied to the in-process OMCI serial-number buffer. **It doesn't rewrite `/proc/ubnthal/sn_raw` or `mtd8`.**
- The modified boot scripts avoid automatically formatting `mtd3` when the configuration mount fails.
- The custom image keeps the original 4.9.0 kernel modules.

The patch was checked under QEMU MIPS (including valid, invalid and missing SN) and a modified 4.9.0 image booted on a UF-INSTANT. **The changed serial number has not yet been verified against a real OLT.** GPON registration was not available during testing (ONU state 0).

# Original and modified images

| Image | Kernel | RootFS |
| --- | --- | --- |
| image0 (`mtd4/mtd5`) | Original Ubiquiti 4.9.0 | Original Ubiquiti 4.9.0 |
| image1 (`mtd6/mtd7`) | Original Ubiquiti 4.9.0 | Modified 4.9.0 |

The source firmware is the official `UF-ONU.UF-INSTANT.v4.9.0.2229-828.241128.1332.img` HIT archive. The kernel is a uImage and the root filesystem is SquashFS 4.0, LZMA, 131072-byte blocks.

# Setting the GPON SN

On the modified image:

```sh
printf '55424e54413d9d11\n' > /var/config/gpon_sn_override
cat /var/config/gpon_sn_override
```

Replace the example SN with the serial number belonging to your own ONU. `omci_app` reads this file **at startup**, so creating it while the process is running won't immediately change its SN. Do not mistake `/proc/ubnthal/sn_raw` for the overridden value; it still reports the original hardware number.

Removing the override file restores the default behaviour on the next OMCI startup:

```sh
rm /var/config/gpon_sn_override
```

`/var/config` is shared between the two images, but original `omci_app` doesn't use this additional file. Keep a backup of `mtd3` before changing any configuration.

# Rebuilding the patch

The source `omci_app` and the 512-byte MIPS `override.bin` are taken from the locally tested 4.9.0 build. `patch_omci.py` applies the hook and checks the full SHA-256 of both the input and the expected output:

```sh
python3 "Firmware 4.9.0/patch_omci.py" \
  patches/omci-4.9.0/omci_app.original \
  patches/omci-4.9.0/override.bin \
  rootfs-4.9.0-mod/bin/omci_app
```

The tested 4.9.0 binaries are **not embedded in this source-only branch**. The command above requires the local build inputs. An unknown payload will fail the final checksum check.

Repack the already prepared modified RootFS on Linux:

```sh
sudo mksquashfs rootfs-4.9.0-mod rootfs-bank1-4.9.0-mod.sqfs \
  -noappend -comp lzma -b 131072 -no-xattrs
```

# Flashing notes

**MAKE SURE TO HAVE A BACKUP OF EACH MTD PARTITION BEFORE PROCEED!**

Do not use `mtd12`/`mtd13` for flashing, they are aliases for the active image. Check `cat /proc/cmdline` and the `sw_active`/`sw_commit` flags first.

On the tested old Realtek kernel, a 4096-byte `dd` write to the MTD character device stopped at the second erase block with `Invalid argument`. **256-byte writes worked**. Always erase only the *inactive* image partitions, and verify the complete content read back from `/dev/mtdblockN` before rebooting. Do not erase `mtd3` or `mtd8` as part of this update.

To try another image without changing the committed one, the tested U-Boot environment uses `sw_tryactive=0` or `1`; `2` boots `sw_commit`. Have UART access before testing a new firmware.

As with the original mod, **all mods are just for fun** and you are responsible for recovery if something goes wrong.

# Missing flash command on 4.9.0

The official 4.9.0 rootfs already contains `/etc/scripts/flash`, but it may not be available in the command PATH. The stock `omci_app` uses `flash get OMCI_FAKE_OK` (and may use `flash set`) and otherwise prints `sh: flash: not found`.

To try this **without flashing anything**, first check the script and create a temporary command link:

```sh
ls -l /etc/scripts/flash
head -n 3 /etc/scripts/flash
ln -s /etc/scripts/flash /tmp/flash
PATH=/tmp:$PATH
export PATH
command -v flash
flash get OMCI_FAKE_OK
```

Note that a PATH change in your SSH shell **does not affect** an already running `omci_app` or the boot scripts. To fix child commands for a running daemon, it must be started with the corrected environment. The temporary `/tmp` link disappears after reboot. For a permanent **image1-only** fix, add a symlink `bin/flash -> ../etc/scripts/flash` to the modified RootFS **before repacking**, or explicitly configure PATH in its launch script. Do not patch the factory image just to perform this test.

This corrects the missing command, but it is **not yet confirmed** to fix the MIB assertion or the `omci_app` abort (exit 134) seen when the fiber is connected. Keep the stick's hardware watchdog protection; do not erase `mtd3` or `mtd8`.
