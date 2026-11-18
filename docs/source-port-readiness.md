# WFOMIXM 306 source port for LineageOS review

Review date: 2026-11-18. Device under review: Redmi Note 14S global
`2502FRA65G` / `glb_r` on `OS3.0.306.0.WFOMIXM`.

## Source starting point

The community `emerald-lineage` 24.0 device tree recognizes the `glb_r` SKU.
Its image contract is for WNFMIXM 305, including its pinned vendor and
three DLKM images. Its 13-partition OTA list omits `mi_ext`. The verified
WFOMIXM 306 full repack uses 14 partitions and includes `mi_ext` in the
dynamic group. A WFOMIXM profile needs its own extraction inputs, init
and mount configuration, recovery modules and VINTF checks.
[Community device tree](https://github.com/emerald-lineage/android_device_xiaomi_emerald/tree/d457692c4e0c87c84b906c995b4a2d4a05032286).

| Input checked against the public 305 kernel tree | Result for WFOMIXM 306 |
| --- | --- |
| Compressed kernel `Image.lz4` | Identical |
| `dtb/mt6789.dtb` | Identical |
| `dtbo.img` | Different |
| 199 stock platform ramdisk modules with matching filenames | All 199 differ |
| Four additional modules in the 305 tree | Review the recovery purpose and dependencies against 306 before inclusion |

These comparisons use Git blob identities computed from the verified 306
inputs and the pinned 305 tree. A separate download of Google's GKI
`Image.lz4` from Android CI build 13847919 matched the 306 stock
`boot.img` kernel. Both were 18,833,091 bytes with SHA-256
`e4121682a5dc9e637710642eb4daaea57697f3b501a959715c4cc323f3e15e35`.
All 82 stock `system_dlkm` modules also matched the same Google build's
flattened module archive by name and SHA-256. The other 408 module files
report two different build revisions in their module metadata. Xiaomi
lists its public Redmi Note 14S kernel and MediaTek modules under
`emerald_r-u-oss` for the Android U base. The kernel branch is 5.10.209.
Corresponding source for the 306 OEM modules remains unverified.
[Community 305 GKI input tree](https://github.com/emerald-lineage/android_device_xiaomi_emerald-kernel/tree/b1b898ae09c29967473099dacb043fd4a0891df2),
[Google GKI artifact](https://ci.android.com/builds/submitted/13847919/kernel_aarch64/latest/Image.lz4),
[Google module archive](https://ci.android.com/builds/submitted/13847919/kernel_aarch64/latest/system_dlkm_staging_archive.tar.gz),
[Google build manifest](https://ci.android.com/builds/submitted/13847919/kernel_aarch64/latest/manifest_13847919.xml),
[Android GKI tag](https://android.googlesource.com/kernel/common/+/refs/tags/android16-6.12-2025-07_r7),
[Public Xiaomi kernel](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/b183d9cceaeb4329781b597e4b520ea6a2687c7a/Makefile),
[Public MediaTek modules](https://github.com/MiCode/MTK_kernel_modules/tree/30a11c8342794e1b681f62939aff836be6ef9278).

Xavero's 24.0 tree is another starting point. Its referenced kernel and
vendor dependencies did not resolve for an anonymous check on the review
date: HTTP 401 for the Halcyon kernel ref listing and HTTP 404 for the
Codeberg vendor repository API. The available 23.2 kernel is a different
5.10 build. Those dependencies need compatible replacements or accessible
corresponding revisions before a clean source build is reproducible.
[Xavero device tree](https://github.com/xaveroprjkt/device_xiaomi_emerald/tree/1d0b28d97f48852f7f298e6e5eb8a6a93fba29b2),
[Android 17 manifest](https://github.com/xaveroprjkt/local_manifests_emerald/blob/8c04c529f3ecc8e5e22c6bfc5e7ccc0299e1fed2/local_manifests.xml).

## LineageOS 24.0 bring-up inputs

Use the [LineageOS 24.0 base manifest](https://github.com/LineageOS/android/blob/913c6baa35ffa32be9ae33368cac69dbec6ead4b/default.xml).
The [local manifest](../source-port/mediatek-lineage-24.0.xml) adds the
official MediaTek hardware and vendor policy repositories at explicit
commits. The following preflight was run in a new checkout on a Linux
filesystem. Set `contribution_repo` to the absolute path of this repository.

```sh
repo init -u https://github.com/LineageOS/android.git \
  -b 913c6baa35ffa32be9ae33368cac69dbec6ead4b --depth=1 --no-clone-bundle
mkdir -p .repo/local_manifests
cp "$contribution_repo/source-port/mediatek-lineage-24.0.xml" \
  .repo/local_manifests/wfomixm-mediatek.xml
repo sync --current-branch --no-tags --no-clone-bundle --fail-fast -j2 \
  hardware/mediatek device/mediatek/sepolicy_vndr tools/extract-utils vendor/lineage
```

Both MediaTek commits matched the manifest. The preflight also checked out
`tools/extract-utils` at `9d3f68fc8d245b7ae72a9bd63ba0ab59e31579f4`
and `vendor/lineage` at `5a1814d916321aecb72d60d13b5e52bc719251bd`.
The latter sets the source branch's target release to `cp2a`. The
device product below resolves with those dependencies in a partial 24.0
checkout.

The [306 mount exclusions](../source-port/wfomixm-306/skip_mount.cfg)
contain the same 21 MIUI overlay destinations from both stock vendor
fstabs. The exclusions retain the base `mi_ext` mount. Install the file
through `PRODUCT_COPY_FILES` to
`$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/init/config/skip_mount.cfg`.
LineageOS's `libfstab` uses this file to filter normal-boot fstab reads
when it is available. The first-stage mount loop defers overlay mounts.
Verify the final mount table on a source-built system.
[LineageOS fstab reader](https://github.com/LineageOS/android_system_fs_fs_mgr/blob/b1dd5c6ccee0aa3019020925204ed72942a822be/libfstab/fstab.cpp),
[first-stage mount implementation](https://github.com/LineageOS/android_system_core/blob/65d661b1a536701e8b118be4e9728d7b5ca727c9/init/first_stage_mount.cpp).

A pilot using the official `extract-utils` copied
`vendor/etc/fstab.mt6789` and `vendor/etc/vintf/manifest.xml` from a
WFOMIXM 306 stock dump. Both extracted files matched their inputs byte for
byte. The tool generated `Android.bp` and `emerald-vendor.mk`. The
complete proprietary file list and extraction from a running
LineageOS build remain to be tested.
[LineageOS guide to proprietary files](https://github.com/LineageOS/lineage_wiki/blob/main/pages/internal/working_with_blobs.md).

Factory `super.img` records 7,516,192,768 bytes for the physical device
and a maximum of 7,505,707,008 bytes for each `main` group. The populated
A set has `odm_dlkm`, `product`, `system`, `system_dlkm`, `system_ext`,
`vendor`, `vendor_dlkm` and `mi_ext`. The matching B entries have zero
allocated bytes in the factory image. Use these values when checking the
new build's super metadata and plan an explicit both-slot test on hardware.

## Configure the WFOMIXM product

The [device configuration](../source-port/wfomixm-306) provides
`lineage_emerald_wfomixm` for the global Redmi Note 14S. It uses intact
stock vendor and DLKM images during bring-up. It keeps ODM under
`vendor/odm`, requires the 199 platform ramdisk modules and uses the stock
boot v4 layout. Its AVB settings use Android test keys. Recovery, signing
and installation still need verification against the generated images.

On Linux, prepare the verified factory images and the kernel bundle with
the [stock input tools](stock-kernel-inputs.md). Point the following
variables to those local inputs and use a new path for the prepared fstabs.
Keep the stock images and generated fstabs outside the public repository.

```sh
export EMERALD_WFOMIXM_IMAGES=/absolute/path/to/stock-images
export EMERALD_WFOMIXM_KERNEL=/absolute/path/to/stock-kernel-bundle
export EMERALD_WFOMIXM_FSTABS=/absolute/path/to/new-fstabs
python3 "$contribution_repo/scripts/stage-wfomixm-fstabs.py" \
  --kernel-bundle "$EMERALD_WFOMIXM_KERNEL" --output "$EMERALD_WFOMIXM_FSTABS"
```

This prepares the platform and recovery fstabs by removing the same 22
stock overlay rows from each. The 22nd target is `/system/framework`.
The remaining bytes are identical, including the base `mi_ext`, user data
and metadata mounts. The separate vendor-fstab policy has 21 destinations.

For the partial-checkout configuration test, sync the host build tools
below in addition to the four projects above. In a full checkout these
are already provided by the manifest. Copy the device files into a new
`device/xiaomi/emerald` directory.

```bash
repo sync --current-branch --no-tags --no-clone-bundle --fail-fast -j3 \
  build/make build/soong build/blueprint build/release \
  prebuilts/go/linux-x86 prebuilts/build-tools prebuilts/bazel/common \
  external/golang-protobuf external/starlark-go external/pogreb \
  frameworks/native toolchain/pgo-profiles device/lineage/sepolicy \
  system/sepolicy external/avb
mkdir -p device/xiaomi/emerald
cp "$contribution_repo/source-port/wfomixm-306/"{AndroidProducts.mk,BoardConfig.mk,lineage_emerald_wfomixm.mk,skip_mount.cfg} \
  device/xiaomi/emerald/
export OUT_DIR=out-emerald-config SKIP_KERNEL_BUILD=true ROOMSERVICE_DRYRUN=true
source build/envsetup.sh
lunch lineage_emerald_wfomixm cp2a userdebug
```

The configuration run resolved Android 17 SDK 37, launch API 34, boot
header v4, the eight logical partitions in `main` and the 14 A/B OTA
partitions. Platform SELinux is `202604` and includes a compatibility
mapping for the stock vendor's `202504`. The resolved product installs
both the ramdisk fstab and the system_ext mount policy. The source target
still needs a full build, VINTF checks against that build, and hardware
validation.

## Export stock vendor and embedded ODM

The [vendor export script](../scripts/export-wfomixm-vendor.py) reads the
verified 306 `vendor.img` through a read-only EROFS mount and writes a
local PAX archive with Android ownership, modes and extended attributes.
It requires GNU tar and permission to mount an EROFS image in a private
mount namespace. WSL users can pass `--wsl-distro` from Windows Python to
select a Linux distribution with those tools.

```sh
sudo python3 scripts/export-wfomixm-vendor.py \
  --vendor-image "$EMERALD_WFOMIXM_IMAGES/vendor.img" \
  --output /absolute/path/to/new-vendor-export
```

The real stock export verified 5,140 files, 740 links and 343 directories,
including embedded ODM. `vendor-inventory.json` records file SHA-256
hashes, literal link targets and SELinux labels. Use this local inventory
to choose the proprietary build inputs and review link and ELF
dependencies. The complete `extract-utils` install list and source-built
vendor rules are still pending. Bring-up with the intact image also needs
the matching vendor and embedded ODM VINTF and APEX metadata in
`target-files` before running `check_target_files_vintf`.

## Design to validate

An A/B source port can build its vendor image from the required stock
files and reviewed sources or document a compatible stock vendor base
for both slots under the project requirements. The community repack
uses a modified prebuilt vendor for charging control. Its matching
Lineage Health source is identified. A source-built vendor can compile
that service as part of the port. The stock-vendor design requires a
separate check of charging control and any other feature that depended
on the repack's vendor changes.
[Vendor requirements](https://github.com/LineageOS/charter/blob/main/device-support-requirements.md#vendor-images),
[Health source](https://github.com/LineageOS/android_hardware_lineage_interfaces/tree/a0f3ada220c573a2252bcb506407b04dfb9b3de0/health/aidl).

A possible community distribution artifact is a partial OTA with
source-built Android partitions and the generated AVB metadata.
Its design would obtain Xiaomi's stock firmware and vendor content
locally, maintain compatible stock partitions on both slots, and account
for root vbmeta, recovery trust and snapshot behavior. The existing
donor-derived system images still contain third-party binaries.
Selecting fewer images from that payload does not establish a new
licensed release or a complete hardware test.
[AOSP OTA generator](https://android.googlesource.com/platform/build/+/android16-qpr2-release/tools/releasetools/ota_from_target_files.py).

## Build and submission evidence

The retained 23.2 checkout contains the downloaded sources and an
incomplete Soong graph. Its last attempt was interrupted during graph
generation, before a target-files package was produced. The validated
24.0 community OTA was a repack. A 24.0 source-built userdebug target,
working proprietary-file extraction, compliant vendor integration, and
recovery/OTA/hardware test evidence are still needed for formal review.
The submission also needs consenting maintainers and links to the exact
device, vendor and kernel trees to be reviewed.
[LineageOS device requirements](https://github.com/LineageOS/charter/blob/main/device-support-requirements.md),
[Submission procedure](https://github.com/LineageOS/lineage_wiki/blob/main/pages/submitting_device.md).
