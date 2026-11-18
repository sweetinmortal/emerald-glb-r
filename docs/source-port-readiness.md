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
inputs and the pinned 305 tree. They establish file identity only.
The generic kernel matches the donor's recorded Google GKI release
identifier and Android CI build 13847919. The donor documents a direct
Google artifact comparison for 305. The original Google download and
complete matching OEM module source remain separate provenance checks.
[Community 305 GKI input tree](https://github.com/emerald-lineage/android_device_xiaomi_emerald-kernel/tree/b1b898ae09c29967473099dacb043fd4a0891df2),
[Android GKI tag](https://android.googlesource.com/kernel/common/+/refs/tags/android16-6.12-2025-07_r7).

Xavero's 24.0 tree is another starting point. Its referenced kernel and
vendor dependencies did not resolve for an anonymous check on the review
date: HTTP 401 for the Halcyon kernel ref listing and HTTP 404 for the
Codeberg vendor repository API. The available 23.2 kernel is a different
5.10 build. Those dependencies need compatible replacements or accessible
corresponding revisions before a clean source build is reproducible.
[Xavero device tree](https://github.com/xaveroprjkt/device_xiaomi_emerald/tree/1d0b28d97f48852f7f298e6e5eb8a6a93fba29b2),
[Android 17 manifest](https://github.com/xaveroprjkt/local_manifests_emerald/blob/8c04c529f3ecc8e5e22c6bfc5e7ccc0299e1fed2/local_manifests.xml).

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
