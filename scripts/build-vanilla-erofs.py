#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Reproduce the verified unsigned WFOMIXM product and system_ext images."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import uuid

import degoogle


REFERENCE = {
    "product": {
        "archive": "product-vanilla.pax.tar",
        "image": "product.unsigned.img",
        "input_sha256": "c1f532c94448ea183492808b3d1a0c81f7bc65c8e53dbf67edb7486e195c9652",
        "image_sha256": "8fdb7334eb8ec97345392d11018a29ac38cfe019ef22bc434657d734de9a3d4a",
    },
    "system_ext": {
        "archive": "system_ext-vanilla.pax.tar",
        "image": "system_ext.unsigned.img",
        "input_sha256": "a0b4e872bc3bd6b1d104bf6dc42f007ce1e12eba23e35ce84455dedc69669ac2",
        "image_sha256": "9ebb460a74ec7b95a674d2ee92b984ee8ebdf4be7cdb5e4f7e733d923545521a",
    },
}

SHA256 = {
    "fsck.erofs": "dd61160aa49a3d63da41ed2ff13e0e42be37d4a09a88f9d459002b2ca0cc2db7",
    "mkfs.erofs": "b254640c783f9626b81b90d483c35d0e998c42113ba1259d1f3f5accfd0dc8e0",
}


def require_hash(path, expected):
    if not path.is_file() or degoogle._sha256_file(path) != expected:
        raise ValueError(f"Unexpected SHA-256 for {path}")


def image_from_archive(scope, spec, source, staging, tools, env):
    archive = source / spec["archive"]
    output = staging / spec["image"]
    filesystem_uuid = str(uuid.uuid5(uuid.NAMESPACE_URL,
                                     f"emerald-vanilla/{scope}/{spec['input_sha256']}"))
    command = [
        tools / "bin/mkfs.erofs", "-z", "lz4hc,9", "--preserve-mtime", "-T", "1230768000",
        "--mkfs-time", "-U", filesystem_uuid, "--tar=f", output, archive,
    ]
    with (staging / f"{scope}-build.log").open("xb") as log:
        for args in (command, [tools / "bin/fsck.erofs", output]):
            check = subprocess.run(args, env=env, stdout=log, stderr=subprocess.STDOUT)
            if check.returncode:
                log.flush()
                tail = log.name
                with open(tail, "rb") as detail:
                    detail.seek(max(0, log.tell() - 4096))
                    message = detail.read().decode(errors="replace")
                raise RuntimeError(f"{scope}: {Path(args[0]).name} failed ({check.returncode})\n{message}")
    require_hash(output, spec["image_sha256"])
    return {"image": output.name, "bytes": output.stat().st_size,
            "sha256": spec["image_sha256"], "input_sha256": spec["input_sha256"],
            "filesystem_uuid": filesystem_uuid}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filtered", type=Path, required=True, help="The two default filtered vanilla PAX archives")
    parser.add_argument("--otatools", type=Path, required=True, help="Extracted AOSP 17 otatools")
    parser.add_argument("--output", type=Path, required=True, help="New output directory on a Linux filesystem")
    args = parser.parse_args()
    filtered, tools, output = map(Path.resolve, (args.filtered, args.otatools, args.output))

    if output.exists():
        raise FileExistsError(output)
    for tool, digest in SHA256.items():
        require_hash(tools / "bin" / tool, digest)
    for item in REFERENCE.values():
        require_hash(filtered / item["archive"], item["input_sha256"])

    env = dict(os.environ, LD_LIBRARY_PATH=str(tools / "lib64"), LC_ALL="C", TZ="UTC")
    with tempfile.TemporaryDirectory(prefix=".emerald-erofs-", dir=output.parent) as tmp:
        staged = Path(tmp) / "images"
        staged.mkdir()
        images = {}
        for scope, spec in REFERENCE.items():
            print(f"Rebuilding {scope}", flush=True)
            images[scope] = image_from_archive(scope, spec, filtered, staged, tools, env)
        report = {"images": images, "tools_sha256": SHA256, "flashable": False}
        (staged / "image-verification.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        staged.rename(output)
    print("Both unsigned EROFS images match the verified reference hashes.")


if __name__ == "__main__":
    main()
