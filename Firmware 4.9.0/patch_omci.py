#!/usr/bin/env python3
"""Add the tested GPON SN override hook to UF-Instant omci_app 4.9.0.

The MIPS payload is assembled separately (override.bin). This script only
installs that payload into unused ELF RX padding and updates the entry hook.
"""
import argparse
import hashlib
from pathlib import Path
import struct

ORIGINAL_SHA256 = "2b8caedef4803c65c6b2016e37f305d20ce2243f5de4ffc4ef0fbeeca1458c95"
PATCHED_SHA256 = "ab06f0e8b644b26ed30d5e1a97ae0e05427fae5202903eb23406e22e46a58568"
CAVE_OFFSET = 0x32A5C
CAVE_VADDR = 0x432A5C
HOOK_OFFSET = 0x5AF0
RX_FILE_SIZE = 0x32F00
RW_OFFSET = 0x33000
ORIGINAL_HOOK = bytes.fromhex("3c1e0043")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def patch(original, payload):
    if sha256(original) != ORIGINAL_SHA256:
        raise ValueError("Wrong omci_app: expected the official 4.9.0 binary")
    if len(payload) != 512:
        raise ValueError("Expected the tested 512-byte MIPS payload")
    if original[HOOK_OFFSET:HOOK_OFFSET + 4] != ORIGINAL_HOOK:
        raise ValueError("Unexpected original hook instruction")
    if any(original[CAVE_OFFSET:RW_OFFSET]):
        raise ValueError("ELF padding is not empty")

    image = bytearray(original)
    if image[:4] != b"\x7fELF" or image[4] != 1 or image[5] != 2:
        raise ValueError("Expected big-endian 32-bit MIPS ELF")
    phoff = struct.unpack_from(">I", image, 28)[0]
    phentsize = struct.unpack_from(">H", image, 42)[0]
    phnum = struct.unpack_from(">H", image, 44)[0]
    rx = None
    for i in range(phnum):
        off = phoff + i * phentsize
        typ, foff, vaddr, _, fsz, msz, flags, _ = struct.unpack_from(">8I", image, off)
        if typ == 1 and foff == 0 and vaddr == 0x400000 and flags & 1:
            if fsz != CAVE_OFFSET or msz != CAVE_OFFSET:
                raise ValueError("Unexpected executable LOAD segment")
            rx = off
            break
    if rx is None:
        raise ValueError("Executable LOAD segment not found")

    image[CAVE_OFFSET:CAVE_OFFSET + len(payload)] = payload
    jump = 0x08000000 | ((CAVE_VADDR >> 2) & 0x03ffffff)
    struct.pack_into(">I", image, HOOK_OFFSET, jump)
    struct.pack_into(">I", image, rx + 16, RX_FILE_SIZE)
    struct.pack_into(">I", image, rx + 20, RX_FILE_SIZE)
    if sha256(image) != PATCHED_SHA256:
        raise ValueError("Payload differs from the device-tested build; nothing written")
    return bytes(image)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("original", type=Path, help="Official 4.9.0 omci_app")
    ap.add_argument("payload", type=Path, help="Locally assembled override.bin")
    ap.add_argument("output", type=Path, help="Patched omci_app destination")
    args = ap.parse_args()
    result = patch(args.original.read_bytes(), args.payload.read_bytes())
    args.output.write_bytes(result)
    args.output.chmod(0o755)
    print(f"{args.output}: {len(result)} bytes, sha256 {sha256(result)}")


if __name__ == "__main__":
    main()
