# Experimental UF-Instant 4.9.0 WebGUI refresh

**Scope:** visually modernize existing ASP pages without rewriting Realtek proprietary ASP callbacks. This is an **offline RootFS patch**, not an independently functioning web server and **not a fix for Boa SIGABRT**. No claims about runtime compatibility are made.

## Install into a working copy of modified bank1 RootFS

From the repository root on Ubuntu:

```bash
cp -a rootfs-4.9.0-mod rootfs-4.9.0-webgui
python3 'Firmware 4.9.0/webgui/install.py' --dry-run rootfs-4.9.0-webgui
python3 'Firmware 4.9.0/webgui/install.py' rootfs-4.9.0-webgui
```

The installer copies CSS into `/home/httpd/web/ufmodern.css`, injects one stylesheet link before `</head>` into existing `*.asp` pages (only those containing `<head>`), and preserves original ASP files as `*.asp.ufmodern.bak`. It does not modify form actions, credentials, scripts, GPON SN, MIB, omci_app or other system libraries.

**RootFS size check before flashing:** With a 4.8 MiB rootfs partition, verify actual image byte count using `stat -c %s`. Extra backup files can increase image size; for a space-constrained final image, keep backups on the Ubuntu host and omit `*.ufmodern.bak` from the filesystem tree used to create the image.

## Test Boa compatibility independently (RAM only)

The 2022 customized Boa requires `libmib.so.0`, `librtk.so` and other Realtek libraries. Loading the two 2022 libraries from `uf-instant-rootfs1/lib` is an **experiment**, not an established fix. Never overwrite `/lib` in the running 4.9.0 system.

On Ubuntu:

```bash
mkdir -p boa-compat/lib
cp -a uf-instant-rootfs1/lib/libmib.so* boa-compat/lib/
cp -a uf-instant-rootfs1/lib/librtk.so* boa-compat/lib/
# Ensure the SONAME filename is present even if archive symlinks were lost:
ls -l boa-compat/lib/
scp -O boa-compat/lib/libmib.so boa-compat/lib/librtk.so ubnt@192.168.1.1:/tmp/
```

On the UF-Instant (via SSH):

```sh
# All writes here target volatile RAM, not MTD.
ls -l /tmp/libmib.so /tmp/librtk.so
ln -s libmib.so /tmp/libmib.so.0
cd /home/httpd
LD_LIBRARY_PATH=/tmp:/lib
export LD_LIBRARY_PATH
/bin/boa -c /var/boa
```

If `/tmp/libmib.so.0` already exists, skip the `ln -s` command. If the loader cannot resolve any additional SONAME, do not copy it into `/lib`; inspect the complete dependency chain offline first. Note that `LD_LIBRARY_PATH` impacts **this shell and its children only**; do not export it globally to `omci_app` or `configd`. Restore a clean environment on reconnect.

If Boa crashes again, the browser cannot use the modernized ASP pages: fix or replace the proprietary Boa backend **before** claiming the update works. The entire compatibility test disappears on reboot.

## Safe deployment strategy

- The existing bank1 rootfs is SquashFS and not editable in-place. Copying an ASP page to `/tmp` does not change the page served from `/home/httpd/web`.
- For a persistent update, build a SquashFS from a working rootfs tree **after** tests. Never flash a filesystem image onto the currently booted `mtd7`.
- Boot original bank0 (`root=31:5`) and only then write the modified bank1 rootfs to **`mtd7`** with the already established device-specific 256-byte write + full readback verification workflow. Keep `mtd6` kernel unchanged.
- Never erase `mtd3` (shared config), `mtd8` (hardware/calibration), or flash using aliases `mtd12/mtd13`. Preserve UART recovery.

This package intentionally does **not** include a flashing script: the legacy Realtek MTD driver requires a device-specific write method and an unverified generic script could brick the module.
