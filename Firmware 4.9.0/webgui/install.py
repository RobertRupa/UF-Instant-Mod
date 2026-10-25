#!/usr/bin/env python3
"""Non-destructive offline UF-Instant ASP skin installer for an unpacked rootfs."""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import sys

CSS_TAG = '<link rel="stylesheet" href="/ufmodern.css" type="text/css" />'
HEAD_CLOSE = re.compile(r"</head\s*>", re.IGNORECASE)
HEAD_OPEN = re.compile(r"<head(?:\s[^>]*)?>", re.IGNORECASE)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("rootfs", type=Path, help="Unpacked modified bank1 rootfs directory")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()
    root = args.rootfs.resolve()
    web = root / "home/httpd/web"
    css = Path(__file__).with_name("modern.css")
    if not (root / "bin/boa").is_file() or not (web / "admin/login.asp").is_file():
        p.error("Expected an unpacked modified UF-Instant rootfs with bin/boa and admin/login.asp")
    candidates = sorted(web.rglob("*.asp"))
    changes = []
    for path in candidates:
        raw = path.read_bytes()
        # Preserve original encoding, custom ASP directives and existing form handlers.
        if b"ufmodern.css" in raw:
            continue
        try:
            txt = raw.decode("latin-1")
        except UnicodeError:
            continue
        match = HEAD_CLOSE.search(txt)
        if not match or not HEAD_OPEN.search(txt):
            continue
        updated = txt[:match.start()] + CSS_TAG + "\n" + txt[match.start():]
        changes.append((path, raw, updated.encode("latin-1")))
    print(f"RootFS: {root}")
    print(f"ASP files: {len(candidates)}; files to update: {len(changes)}")
    for path, _, _ in changes:
        print("  ", path.relative_to(root))
    if args.dry_run:
        return 0
    css_dest = web / "ufmodern.css"
    if css_dest.exists() and css_dest.read_bytes() != css.read_bytes():
        p.error("Existing ufmodern.css differs; refusing to overwrite it")
    for path, original, updated in changes:
        backup = path.with_suffix(path.suffix + ".ufmodern.bak")
        if backup.exists() and backup.read_bytes() != original:
            p.error(f"Backup already exists with differing contents: {backup}")
    for path, original, updated in changes:
        backup = path.with_suffix(path.suffix + ".ufmodern.bak")
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_bytes(updated)
    shutil.copy2(css, css_dest)
    print("Installed CSS and updated ASP references. Original ASP backed up as *.ufmodern.bak")
    print("IMPORTANT: This does not fix Boa SIGABRT or change MIB/OMCI binaries.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
