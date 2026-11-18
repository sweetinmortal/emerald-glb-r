#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

"""Prepare the Redmi Note 14S ramdisk fstab inputs from a verified stock bundle."""

import argparse
import hashlib
from pathlib import Path
import tempfile


STOCK_FSTABS = {
    "fstab.mt6789": ("platform-ramdisk", "522842d9cfb336f8685c10e58e919e5049cc23b90b12eb753a81a49a2df20739"),
    "fstab.emmc": ("recovery-ramdisk", "96c06a6e49d3605d0ed11e0fea038ecfb2ef035de04bbfc7290e770d0b560e72"),
}
POLICY = Path(__file__).resolve().parents[1] / "source-port/wfomixm-306/skip_mount.cfg"


def without_miui_overlays(data, expected_mounts):
    selected = []
    result = []
    for line in data.splitlines(keepends=True):
        fields = line.partition(b"#")[0].split()
        if len(fields) >= 3 and fields[2] == b"overlay":
            destination = fields[1]
            lower = (b"/product/pangu/system/framework/" if destination == b"/system/framework"
                     else b"/mnt/vendor/mi_ext/")
            if len(fields) < 4 or b"lowerdir=" + lower not in fields[3]:
                raise ValueError("Unexpected fstab overlay source")
            selected.append(destination)
        else:
            result.append(line)
    if len(selected) != len(expected_mounts) or set(selected) != expected_mounts:
        raise ValueError("Unexpected fstab overlay destinations")
    return b"".join(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernel-bundle", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)

    # The two ramdisk fstabs also overlay /system/framework.
    mounts = set(POLICY.read_bytes().splitlines()) | {b"/system/framework"}
    files = {}
    for name, (ramdisk, digest) in STOCK_FSTABS.items():
        source = args.kernel_bundle / "modules" / ramdisk / "first_stage_ramdisk" / name
        data = source.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"Unexpected stock fstab contents: {source}")
        files[name] = without_miui_overlays(data, mounts)

    with tempfile.TemporaryDirectory(prefix=".wfomixm-fstabs-", dir=output.parent) as scratch:
        result = Path(scratch) / "fstabs"
        result.mkdir()
        for name, data in files.items():
            (result / name).write_bytes(data)
        result.rename(output)
    print(f"Staged {len(files)} fstabs with {len(mounts)} MIUI overlay destinations removed from each.")


if __name__ == "__main__":
    main()
