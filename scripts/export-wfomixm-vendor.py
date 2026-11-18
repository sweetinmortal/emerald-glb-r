#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""Export an untouched WFOMIXM 306 vendor partition and inventory its filesystem."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import tarfile
import tempfile

from degoogle import _sha256_file
from stock_erofs import TAR, mount_command


MANIFEST = Path(__file__).with_name("ota-inputs.json")
COUNTS = {"regular": 5140, "symlink": 740, "directory": 343}


def inventory(archive):
    records = {}
    counts = Counter()
    with tarfile.open(archive, "r:") as tree:
        for entry in tree:
            path = PurePosixPath(entry.name)
            if path.is_absolute() or ".." in path.parts or path.as_posix() in records:
                raise ValueError(f"Unexpected vendor archive path {entry.name}")
            kind = {tarfile.REGTYPE: "regular", tarfile.DIRTYPE: "directory",
                    tarfile.SYMTYPE: "symlink"}.get(entry.type)
            attrs = entry.pax_headers
            label = attrs.get("SCHILY.xattr.security.selinux", "").rstrip("\0")
            if kind is None or not label:
                raise ValueError(f"Invalid type or missing SELinux label for {entry.name}")

            record = {"type": kind, "uid": entry.uid, "gid": entry.gid, "mode": f"{entry.mode:04o}",
                      "selinux": label, "xattrs": sorted(key.removeprefix("SCHILY.xattr.") for key in attrs
                                                       if key.startswith("SCHILY.xattr."))}
            if entry.isfile():
                with tree.extractfile(entry) as data:
                    record["size"] = entry.size
                    digest = hashlib.sha256()
                    for chunk in iter(lambda: data.read(1024**2), b""):
                        digest.update(chunk)
                    record["sha256"] = digest.hexdigest()
            elif entry.issym():
                record["target"] = entry.linkname
            counts[kind] += 1
            records[path.as_posix()] = record
    if counts != COUNTS:
        raise ValueError(f"Unexpected stock vendor entry counts: {dict(counts)}")
    if records.get("odm/etc/build_glb_r.prop", {}).get("type") != "regular":
        raise ValueError("Missing embedded global Redmi Note 14S ODM properties")
    return dict(counts), records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vendor-image", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--wsl-distro", help="WSL distro with EROFS support and GNU tar")
    args = parser.parse_args()

    vendor = args.vendor_image.resolve()
    output = args.output.absolute()
    expected = json.loads(MANIFEST.read_bytes())["xiaomi"]["images"]["vendor"]
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    if vendor.stat().st_size != expected["size_bytes"] or _sha256_file(vendor) != expected["sha256"]:
        raise ValueError("Unexpected WFOMIXM vendor image")
    if shutil.disk_usage(output.parent).free < 3 * 1024**3:
        raise OSError("Allow at least 3 GiB for the vendor export")

    with tempfile.TemporaryDirectory(prefix=".wfomixm-vendor-", dir=output.parent) as scratch:
        staged = Path(scratch) / "vendor"
        staged.mkdir()
        path = staged / "vendor.pax.tar"
        with path.open("xb") as raw:
            subprocess.run(mount_command(args.wsl_distro, vendor, *TAR), stdout=raw, check=True)

        counts, entries = inventory(path)
        report = {"firmware": "OS3.0.306.0.WFOMIXM", "vendor_image_sha256": expected["sha256"],
                  "archive_sha256": _sha256_file(path), "entry_counts": counts,
                  "embedded_odm": "odm/", "entries": entries}
        (staged / "vendor-inventory.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        staged.rename(output)
    print(f"Verified metadata and content for {sum(counts.values())} entries. Stock contents stay local.")


if __name__ == "__main__":
    main()
