#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stage hash-pinned Redmi Note 14S ROM inputs from local downloads."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import zipfile


MANIFEST = Path(__file__).with_name("ota-inputs.json")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024**2), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_size(path, size):
    if path.stat().st_size != size:
        raise ValueError(f"Unexpected size for {path}")


def payload_offset(path, inputs):
    verify_size(path, inputs["size_bytes"])
    expected_zip = inputs.get("sha256")
    if expected_zip is not None and sha256(path) != expected_zip:
        raise ValueError(f"Unexpected ZIP SHA-256 for {path}")

    with zipfile.ZipFile(path) as archive:
        entries = [entry for entry in archive.infolist() if entry.filename == "payload.bin"]
        if len(entries) != 1 or entries[0].compress_type != zipfile.ZIP_STORED:
            raise ValueError(f"Expected one stored payload.bin in {path}")
        entry = entries[0]
        with archive.open(entry) as payload:
            header = payload.read(24)
            if len(header) != 24:
                raise ValueError(f"Truncated payload header in {path}")
            magic, version, manifest_size, signature_size = struct.unpack(">4sQQI", header)
            if (magic != b"CrAU" or version != 2
                    or not 0 < manifest_size < 64 * 1024**2
                    or not 0 < signature_size < 1024**2
                    or 24 + manifest_size + signature_size >= entry.file_size):
                raise ValueError(f"Unexpected payload header in {path}")
            if "payload_manifest_sha256" in inputs:
                if manifest_size != inputs["payload_manifest_size_bytes"]:
                    raise ValueError(f"Unexpected payload manifest size in {path}")
                manifest = payload.read(manifest_size)
                if hashlib.sha256(manifest).hexdigest() != inputs["payload_manifest_sha256"]:
                    raise ValueError(f"Unexpected payload manifest digest in {path}")

    with path.open("rb") as stream:
        stream.seek(entry.header_offset)
        header = stream.read(30)
    if len(header) != 30 or header[:4] != b"PK\x03\x04":
        raise ValueError(f"Unexpected ZIP local header in {path}")
    return entry.header_offset + 30 + sum(struct.unpack_from("<HH", header, 26))


def extract(extractor, ota, offset, folder, images):
    folder.mkdir()
    subprocess.run([
        extractor, f"--payload={ota}", f"--payload_offset={offset}",
        f"--output_dir={folder}", "--partitions=" + ",".join(images),
    ], check=True)
    if {path.name for path in folder.iterdir()} != {name + ".img" for name in images}:
        raise ValueError(f"Unexpected output image set from {ota}")


def verify_images(folder, images):
    for name, info in images.items():
        path = folder / (name + ".img")
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Expected a regular image for {name}")
        verify_size(path, info["size_bytes"])
        if sha256(path) != info["sha256"]:
            raise ValueError(f"Unexpected SHA-256 for {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    stock = parser.add_mutually_exclusive_group(required=True)
    stock.add_argument("--stock-ota", type=Path)
    stock.add_argument("--stock-images", type=Path, help="Directory of previously extracted WFOMIXM images")
    parser.add_argument("--donor-ota", type=Path, required=True)
    parser.add_argument("--ota-extractor", help="Path to AOSP ota_extractor", default="ota_extractor")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    sources = {"donor": args.donor_ota.resolve()}
    if args.stock_ota:
        sources["xiaomi"] = args.stock_ota.resolve()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    offsets = {name: payload_offset(path, manifest[name]) for name, path in sources.items()}

    with tempfile.TemporaryDirectory(prefix=".emerald-inputs-", dir=output.parent) as tmp:
        staging = Path(tmp) / "bundle"
        staging.mkdir()
        for name, path in sources.items():
            images = manifest[name]["images"]
            extract(args.ota_extractor, path, offsets[name], staging / name, images)
            verify_images(staging / name, images)
        if args.stock_images:
            stock_folder = staging / "xiaomi"
            stock_folder.mkdir()
            stock_images = manifest["xiaomi"]["images"]
            for name, info in stock_images.items():
                filename = name + ".img"
                source = args.stock_images / filename
                if source.is_symlink() or not source.is_file():
                    raise ValueError(f"Expected a regular image for {source}")
                verify_size(source, info["size_bytes"])
                shutil.copyfile(source, stock_folder / filename)
            verify_images(stock_folder, stock_images)
        report = {"inputs": manifest, "stock_input_mode": "ota" if args.stock_ota else "images",
                  "image_hashes_verified": True, "flashable": False}
        (staging / "verified-inputs.json").write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8")
        staging.rename(output)

    count = sum(len(source["images"]) for source in manifest.values())
    print(f"Verified {count} local images in {output}")


if __name__ == "__main__":
    main()
