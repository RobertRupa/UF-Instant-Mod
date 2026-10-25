#!/usr/bin/env bash
set -Eeuo pipefail
cd "$(dirname "$0")/../../"
SRC="${1:-rootfs-4.9.0-mod}"
DST="${2:-rootfs-4.9.0-cli-only}"
IMG="${3:-rootfs-bank1-cli-only.sqfs}"
[[ -d "$SRC" && -f "$SRC/etc/init.d/rcS" && -x "$SRC/bin/omci_app" ]] || { echo "Missing prepared 4.9.0 modified RootFS: $SRC" >&2; exit 1; }
[[ ! -e "$DST" ]] || { echo "Destination exists; refusing overwrite: $DST" >&2; exit 1; }
command -v mksquashfs >/dev/null || { echo "Install squashfs-tools"; exit 1; }
cp -a "$SRC" "$DST"
python3 "Firmware 4.9.0/cli-only/patch_rootfs.py" "$DST"
sudo mksquashfs "$DST" "$IMG" -noappend -comp lzma -b 131072 -no-xattrs >/dev/null
bytes=$(stat -c %s "$IMG")
(( bytes <= 4915200 && bytes > 0 && bytes % 256 == 0 )) || { echo "Image size $bytes invalid for mtd7 or 256-byte writes" >&2; exit 1; }
echo "Image: $IMG ($bytes bytes)"
sha256sum "$IMG"
md5sum "$IMG"
echo "NEXT: Boot original bank0 (root=31:5) then use flash-bank1.sh $IMG"
