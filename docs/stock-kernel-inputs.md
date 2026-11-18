# Prepare the stock 6.12 kernel inputs

This procedure extracts the matched kernel, device trees and module inputs used
in the Redmi Note 14S global test. It runs on a Linux PC or in a Linux container,
using partition images from a local copy of the
[Xiaomi full OTA for `OS3.0.306.0.WFOMIXM`](https://bigota.d.miui.com/OS3.0.306.0.WFOMIXM/emerald_r_global-ota_full-OS3.0.306.0.WFOMIXM-user-16.0-2c23fa0a2a.zip).

Use a payload extractor that supports Android full OTAs to extract these six raw
images from the OTA's `payload.bin`.

| Directory | Files |
| --- | --- |
| Boot images | `boot.img`, `vendor_boot.img`, `dtbo.img` |
| Module images | `system_dlkm.img`, `vendor_dlkm.img`, `odm_dlkm.img` |

The two directory arguments can point to the same folder when all six images
were extracted together. The tool checks each image's SHA-256 against the exact
stock version this port uses before processing it. Use an existing parent
directory on a Linux filesystem for the output, with a new name for the bundle.

Run from the repository root with Python 3.10 or newer, `lz4`, `fdtoverlay`
(from device-tree-compiler), `modinfo` (from kmod), and an EROFS
`fsck.erofs` that supports both `--extract` and `--no-preserve`.

```sh
python3 scripts/prepare-stock-kernel-612.py \
  --boot-images /path/to/boot-images \
  --module-images /path/to/module-images \
  --output /path/to/stock-kernel-bundle
```

The tool preserves the input files and writes the output directory once the
checks succeed. The bundle contains the compressed kernel, stock boot image
body, DTB/DTBO, bootconfig, module trees, DLKM images and mount layout. It records
input hashes and module metadata in `bundle.json` and output hashes in
`SHA256SUMS`. You can verify the output with `sha256sum -c SHA256SUMS` from
inside the bundle directory.

The reference run checked all six inputs, both forms of the kernel, a DTB/DTBO
merge and 490 module files. It matched 515 artifact hashes from the earlier
integration bundle and reproduced the same report data. The report records the
408 module files whose embedded build release differs from the GKI release.
Full module ABI validation and ROM-level boot, AVB and recovery testing remain
separate. Use this output as local build input. The tool does not build or sign
an OTA, connect to a phone or produce a flashable package.

See the [binary provenance review](redistribution.md) before redistributing
files extracted from this OTA.
