# Local inputs for the Redmi Note 14S vanilla repack

These steps cover the input and archive preparation stages for model
`2502FRA65G`, SKU `glb_r`, on stock `OS3.0.306.0.WFOMIXM`.

Obtain the two release archives from their original distributors. Use the
full RamDll OTA rather than its incremental or images-and-tools download.
[Xiaomi WFOMIXM full OTA](https://bigota.d.miui.com/OS3.0.306.0.WFOMIXM/emerald_r_global-ota_full-OS3.0.306.0.WFOMIXM-user-16.0-2c23fa0a2a.zip) ·
[RamDll 2.20 release](https://github.com/RamDll/emerald-ota/releases/tag/2.20).

## Verify and extract the input images

Use Python 3.10 or newer and an Android AOSP `ota_extractor` with
`--partitions` and `--payload_offset`. Run it on Linux or in WSL2, with the
matching host libraries needed by your build of the executable. Keep the
inputs and outputs in local storage, with at least 10 GiB available in
addition to the original downloads for the extracted images and archives.
For a container or WSL2, working on its native Linux filesystem avoids
slow random writes through a Windows bind mount during payload extraction.

```sh
python3 scripts/stage-ota-inputs.py \
  --stock-ota /path/to/WFOMIXM.zip \
  --donor-ota /path/to/lineage-24.0-2.20-emerald-signed-ota.zip \
  --output /path/to/verified-inputs
```

The tool checks the donor ZIP's SHA-256, the stock ZIP's payload manifest
and the byte count and SHA-256 of every extracted image. If you already
have the 11 exact raw stock images, use `--stock-images /path/to/stock`
instead of `--stock-ota`. The same per-image checks apply when copying
those local files into the output. See the
[download and image manifest](../scripts/ota-inputs.json) for exact hashes.
The staging tool keeps the donor and stock trees in separate directories.
The donor `vendor_boot.img` is an input for later ramdisk comparison.

## Prepare the product and system_ext archives

On Linux this operation needs read-only EROFS and loop mounts, a private
mount namespace and GNU tar with extended-attribute support. Run from the
repository root.

```sh
sudo python3 -B scripts/prepare-vanilla-archives.py \
  --inputs /path/to/verified-inputs \
  --output /path/to/prepared-pax
```

On Windows you can run this stage with Windows Python and
`--wsl-distro YOUR_DISTRO` using Windows drive paths. The named WSL2
distribution must provide EROFS, loop devices, GNU tar and the util-linux
mount and namespace tools. It performs the mounts as root in an isolated
mount namespace. The mounts are read-only with device nodes, execution and
setuid disabled. The script streams the archives to the output directory
and preserves metadata, including SELinux labels.

The result removes the donor Updater and its server URI, adds the
WFOMIXM compatibility matrix, and derives the tested 21 mount exclusions
from the two stock fstabs. Feed the output `product.pax.tar` and
`system-ext.pax.tar` into the [vanilla removal procedure](vanilla.md).
Use the plan hash printed for this run, since the plan includes the input
paths. The stock kernel helper can use the `xiaomi` directory for both of
its input directory arguments. [Kernel input procedure](stock-kernel-inputs.md).

Both prepared PAX files matched the SHA-256 values of the archives used
for the original experimental build.

## Remaining packaging work

A full OTA also needs the EROFS image build, patched vendor and recovery
assembly, APEX metadata regeneration, aligned AVB and OTA signatures, and
payload replay. The exact charging-control binaries came from the
LineageOS Health sources documented by the device tree. A local rebuild
must account for these inputs and regenerate all signing metadata with
the builder's own identities. [Health prebuilt provenance](https://github.com/emerald-lineage/android_device_xiaomi_emerald/blob/d457692c4e0c87c84b906c995b4a2d4a05032286/prebuilts/lineage-health/README.md).

To offer future automatic updates to users of a centrally distributed build,
ship an Updater configured for this variant with a project-controlled feed
and a release identity accepted by the installed system and recovery. A
separately signed personal build needs updates signed by its own trusted
identity. Delivery of the experimental package and of automated updates
remains pending. [LineageOS Updater](https://github.com/LineageOS/android_packages_apps_Updater)
and [Android OTA signing](https://source.android.com/docs/core/ota/sign_builds).
