# Publication status

GitHub holds the code, test evidence and issue history. The Pre-Alpha
SourceForge project hosts the [experimental tester release](https://sourceforge.net/projects/emerald-glb-r/files/experimental-20261118/).
The release folder contains the ZIP, its test scope and SHA256SUMS.

## Source contribution

The repository contains the Google-app removal tool and its manifest/tests,
sanitized filesystem/OTA/DSU results, compatibility notes and the reviewed
Dolby source patch. It contains no private signing material, firmware images
or application binaries. The Dolby patch remains separate from the candidate. The
[stock kernel preparation tool](stock-kernel-inputs.md) uses local images from
Xiaomi's OTA to assemble and verify the matched 6.12 inputs.

The [local repack procedure](local-repack.md) stages verified input images
and prepares the product and system_ext archives.

The archive-filtering steps are portable with explicit archive paths. The
manifest's historical default paths document its original inputs. The remaining
image rebuilding, signing and packaging helpers still need a portable public
interface; this repository does not yet reproduce the entire ROM from a clean
checkout. Original build reports keep their historical timestamps and scope.

## Experimental tester ZIP

- File: `lineage-24.0-emerald-glb_r-WFOMIXM-VANILLA-HEALTH-EXPERIMENTAL.zip`
- Bytes: `2302608962` (about 2.14 GiB)
- SHA-256: `40f02607109901981b1b2f1e1747abd4d2998f80501835476598dd6de664f9f1`
- Target tested: Redmi Note 14S global, model `2502FRA65G`, `glb_r`,
  `emerald_r_global`, stock base `OS3.0.306.0.WFOMIXM`.
- Composition: RamDll 2.20 userspace adapted to the WFOMIXM hardware base,
  Android 17 / LineageOS 24.0, stock kernel 6.12.30, vendor charging-control
  additions, GApps removal with the documented retained components.

The ZIP passed offline signature, AVB, partition-replay and APEX metadata
checks. DSU validated its userspace, setup and QR scanner with separate data.
That guest used the host's kernel and Magisk-patched vendor_boot. It did not
validate recovery installation of the complete ZIP, the candidate's clean
vendor_boot, a new root vbmeta chain or the Virtual A/B merge path.

The experiment is available to testers. Before recommending general installation:

1. Validate the complete installation and return/recovery procedure on the
   exact supported hardware, with data loss explicitly acceptable for that test.
   The current owner's personal installation is not disposable test data.
2. Document the required recovery/boot artifacts and exact installation steps
   from that successful test. There are no public flashing commands in this
   document while the procedure remains unvalidated.
3. Resolve the remaining source and license questions in the
   [binary provenance review](redistribution.md). The payload excludes the
   eleven named firmware partitions and still includes proprietary components
   in vendor and other images.
4. Update the release notes and SHA256SUMS when a fully tested artifact
   replaces this experimental ZIP.

Dolby's first-boot migration crash and the open thermal investigation are known
limitations. The source fix for Dolby is not in the ZIP. Its original signed APK
is retained; the local OTA key cannot replace its platform/shared-UID signer.

## Hosting

SourceForge's [release-file documentation](https://sourceforge.net/p/forge/documentation/Release%20Files%20for%20Download/)
describes resumable transfers and a 10 GB per-file mirror limitation. This ZIP
fits without splitting. The project must also meet SourceForge's
[open-source hosting requirements](https://sourceforge.net/p/forge/documentation/Create%20a%20New%20Project/).
The published test scope and the remaining validation are documented above.
