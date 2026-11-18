#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Extract verified stock Redmi Note 14S build inputs from Xiaomi's fastboot archive."""

import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tarfile
import tempfile

import degoogle


FIRMWARE = "OS3.0.306.0.WFOMIXM"
FACTORY_ARCHIVE_BYTES = 8_692_703_586
FACTORY_ARCHIVE_SHA256 = "92a4c3f73a4d8c75a75c1ccd17c8cedc8161379731c6e387b65181454f943afe"
FACTORY_IMAGES = "emerald_r_global_images_OS3.0.306.0.WFOMIXM_16.0/images/"
LOGICAL = ("mi_ext", "odm_dlkm", "system_dlkm", "vendor", "vendor_dlkm")
MANIFEST = Path(__file__).with_name("ota-inputs.json")


def extract_members(archive, requested):
    copied = set()
    with tarfile.open(archive, "r|gz", bufsize=1024**2) as tar:
        for member in tar:
            if member.name not in requested:
                continue
            target = requested[member.name]
            if not member.isfile() or member.name in copied:
                raise ValueError(f"Unexpected factory tar entry {member.name}")
            print(f"Extracting {target.name}", flush=True)
            with tar.extractfile(member) as marked_image, target.open("xb") as output:
                shutil.copyfileobj(marked_image, output, length=8 * 1024**2)
            if target.stat().st_size != member.size:
                raise ValueError(f"Truncated factory image {member.name}")
            copied.add(member.name)
    if requested.keys() != copied:
        raise ValueError("Missing requested factory images: " + ", ".join(sorted(requested.keys() - copied)))


def extract_super(sparse, staging, tools):
    with sparse.open("rb") as stream:
        if stream.read(4) != struct.pack("<I", 0xED26FF3A):
            raise ValueError("Expected an Android sparse super image")
    raw = staging / "super.raw.img"
    env = dict(os.environ, LD_LIBRARY_PATH=str(tools / "lib64"))
    print("Converting sparse super", flush=True)
    subprocess.run([tools / "bin/simg2img", sparse, raw], env=env, check=True)
    logical = staging / "logical"
    logical.mkdir()
    flags = [f"--partition={name}_a" for name in LOGICAL]
    print("Extracting logical partitions from super", flush=True)
    subprocess.run([tools / "bin/lpunpack", *flags, raw, logical], env=env, check=True)
    return logical


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--factory-archive", required=True, type=Path, help="Verified Xiaomi WFOMIXM fastboot TGZ")
    parser.add_argument("--otatools", required=True, type=Path, help="AOSP Linux otatools directory with simg2img and lpunpack")
    parser.add_argument("--output", required=True, type=Path, help="New stock build input directory")
    args = parser.parse_args()
    archive, tools, output = map(Path.resolve, (args.factory_archive, args.otatools, args.output))
    if output.exists():
        raise FileExistsError(output)
    if (not archive.is_file() or archive.stat().st_size != FACTORY_ARCHIVE_BYTES
            or degoogle._sha256_file(archive) != FACTORY_ARCHIVE_SHA256):
        raise ValueError("The factory archive does not match the WFOMIXM input")
    for name in ("simg2img", "lpunpack"):
        if not (tools / "bin" / name).is_file():
            raise FileNotFoundError(f"Missing AOSP executable {name}")
    reference = json.loads(MANIFEST.read_bytes())["xiaomi"]["images"]

    with tempfile.TemporaryDirectory(prefix=".emerald-fastboot-", dir=output.parent) as tmp:
        scratch = Path(tmp)
        result = scratch / "images"
        result.mkdir()
        wanted = {FACTORY_IMAGES + f"{name}.img": result / f"{name}.img"
                  for name in reference.keys() - set(LOGICAL)}
        sparse = scratch / "super.sparse.img"
        wanted[FACTORY_IMAGES + "super.img"] = sparse
        extract_members(archive, wanted)
        logical = extract_super(sparse, scratch, tools)
        for name in LOGICAL:
            (logical / f"{name}_a.img").rename(result / f"{name}.img")

        images = {}
        for name, expected in reference.items():
            image = result / f"{name}.img"
            size = image.stat().st_size
            digest = degoogle._sha256_file(image)
            if digest != expected["sha256"] or size != expected["size_bytes"]:
                raise ValueError(f"Factory {name} differs from the pinned OTA size or hash: {size}, {digest}")
            images[name] = {"file": image.name, "bytes": size, "sha256": digest}
            print(f"{name} matches pinned OTA", flush=True)
        report = {"firmware": FIRMWARE, "factory_archive_sha256": FACTORY_ARCHIVE_SHA256,
                  "super_metadata_slot": 0, "images": images, "build_inputs_only": True}
        (result / "verified-stock.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        result.rename(output)
    print(f"Verified {len(images)} factory images against the full OTA contract.")


if __name__ == "__main__":
    main()
