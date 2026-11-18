#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare the two local PAX inputs to the vanilla removal tool."""

import argparse
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile

import degoogle
from stock_erofs import TAR, mount_command


META = Path(__file__).with_name("ota-inputs.json")
VINTF = Path(__file__).with_name("compatibility_matrix.wfomixm_diagnostic.xml")
MATRIX = "etc/vintf/" + VINTF.name
SYSTEM_FILE = "u:object_r:system_file:s0"
UPDATER = "priv-app/Updater"
CONFIG_DIR = "etc/init/config"
CONFIG = CONFIG_DIR + "/skip_mount.cfg"
UPDATER_PROPERTY = b"lineage.updater.uri=https://raw.githubusercontent.com/RamDll/emerald-ota/main/emerald/{incr}.json"

def verify_image(bundle, source, name, manifest):
    path = bundle / source / (name + ".img")
    info = manifest[source]["images"][name]
    if (not path.is_file() or path.is_symlink() or path.stat().st_size != info["size_bytes"]
            or degoogle._sha256_file(path) != info["sha256"]):
        raise ValueError(f"Incorrect source image {source}/{name}")
    return path


def overlay_paths(fstab):
    rows = [line.split() for line in fstab.splitlines()
            if line.strip() and not line.lstrip().startswith("#")]
    selected = [row for row in rows if row[2] == "overlay" and "/mi_ext/" in row[3]]
    paths = {row[1] for row in selected}
    if (len(selected) != 21 or len(paths) != 21
            or any(row[1] in paths for row in rows if row not in selected)
            or any(not path.startswith(("/product/", "/system/", "/system_ext/"))
                   or any(char in path for char in "*?[") for path in paths)):
        raise ValueError("Unexpected overlay entries in the stock fstab")
    return paths


def stock_mount_exclusions(distro, vendor):
    contents = subprocess.check_output(mount_command(
        distro, vendor, "sh", "-c", "cat etc/fstab.emmc; printf '\\000'; cat etc/fstab.mt6789"
    )).decode("utf-8")
    emmc, mt6789 = contents.split("\0")
    paths = overlay_paths(emmc)
    if paths != overlay_paths(mt6789):
        raise ValueError("The stock fstab overlay lists differ")
    config = ("\n".join(sorted(paths)) + "\n").encode("ascii")
    if hashlib.sha256(config).hexdigest() != "255cfc517a7de7c50cd3bfbf1241de87cbf3aba6e8c5db48a9e0936f492cc729":
        raise ValueError("Mount exclusions differ from the tested port")
    return config


def add_from_directory(output, template, name, data=None):
    if (not template.isdir() or (template.uid, template.gid) != (0, 0)
            or template.pax_headers.get("SCHILY.xattr.security.selinux", "").rstrip("\0") != SYSTEM_FILE):
        raise ValueError(f"Unexpected metadata for the parent of {name}")
    entry = copy.copy(template)
    entry.name = "./" + name
    entry.type = tarfile.DIRTYPE if data is None else tarfile.REGTYPE
    entry.mode = 0o755 if data is None else 0o644
    entry.size = 0 if data is None else len(data)
    entry.pax_headers = {key: value for key, value in template.pax_headers.items()
                         if key.startswith("SCHILY.xattr.")}
    output.addfile(entry, None if data is None else io.BytesIO(data))


def remove_update_uri(archive, member, output):
    if not member.isfile():
        raise ValueError("Donor product build properties are missing")
    properties = archive.extractfile(member).read()
    lines = properties.splitlines(keepends=True)
    if lines.count(UPDATER_PROPERTY + b"\n") != 1:
        raise ValueError("Unexpected updater URI in donor product build properties")
    data = b"".join(line for line in lines if line != UPDATER_PROPERTY + b"\n")
    member = copy.copy(member)
    member.size = len(data)
    member.pax_headers = {key: value for key, value in member.pax_headers.items() if key != "size"}
    output.addfile(member, io.BytesIO(data))


def export(distro, image, output, *, scope, additions, template_name):
    seen = set()
    template = None
    with subprocess.Popen(mount_command(distro, image, *TAR), stdout=subprocess.PIPE) as reader:
        try:
            with tarfile.open(fileobj=reader.stdout, mode="r|") as source, \
                    tarfile.open(output, "x", format=tarfile.PAX_FORMAT) as result:
                for entry in source:
                    name = degoogle._canonical_name(entry.name)
                    if name in seen or name in additions:
                        raise ValueError(f"Unexpected duplicate or preexisting {scope} path: {name}")
                    seen.add(name)
                    if name == template_name:
                        template = entry
                    if scope == "product" and name == "etc/build.prop":
                        remove_update_uri(source, entry, result)
                    elif scope != "system_ext" or not (name == UPDATER or name.startswith(UPDATER + "/")):
                        result.addfile(entry, source.extractfile(entry) if entry.isfile() else None)
                expected = "etc/build.prop" if scope == "product" else UPDATER + "/Updater.apk"
                if template is None or expected not in seen:
                    raise ValueError(f"Missing expected entries in {scope}")
                if scope == "system_ext" and CONFIG_DIR not in seen:
                    add_from_directory(result, template, CONFIG_DIR)
                for name, data in additions.items():
                    add_from_directory(result, template, name, data)
            while reader.stdout.read(65536):
                pass
            if reader.wait() != 0:
                raise RuntimeError(f"Read-only export failed for {scope}")
        except BaseException:
            if reader.poll() is None:
                # Closing the pipe lets tar fail and the shell unmount its image.
                reader.stdout.close()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True, type=Path, help="Directory produced by stage-ota-inputs.py")
    parser.add_argument("--output", required=True, type=Path, help="New directory to contain the two PAX archives")
    parser.add_argument("--wsl-distro", help="WSL 2 distro to use for read-only mounts from Windows")
    args = parser.parse_args()
    if (os.name == "nt") != bool(args.wsl_distro):
        parser.error("--wsl-distro is required on Windows and applies only to Windows")

    manifest = json.loads(META.read_bytes())
    bundle, output = args.inputs.resolve(), args.output.resolve()
    if output.exists():
        raise FileExistsError(output)
    product = verify_image(bundle, "donor", "product", manifest)
    system_ext = verify_image(bundle, "donor", "system_ext", manifest)
    vendor = verify_image(bundle, "xiaomi", "vendor", manifest)
    matrix = VINTF.read_bytes().replace(b"\r\n", b"\n")
    config = stock_mount_exclusions(args.wsl_distro, vendor)
    if hashlib.sha256(matrix).hexdigest() != "6232ba8b4f79bd4f3e41e24528db390b954e196158d07152d584f84057bcdb95":
        raise ValueError("Unexpected VINTF matrix content")

    with tempfile.TemporaryDirectory(prefix=".emerald-pax-", dir=output.parent) as tmp:
        staging = Path(tmp) / "archives"
        staging.mkdir()
        export(args.wsl_distro, product, staging / "product.pax.tar", scope="product",
               additions={MATRIX: matrix}, template_name="etc/vintf")
        export(args.wsl_distro, system_ext, staging / "system-ext.pax.tar", scope="system_ext",
               additions={CONFIG: config}, template_name="etc/init")
        staging.rename(output)
    print(f"Prepared PAX archives for the local Google-app removal step in {output}")


if __name__ == "__main__":
    main()
