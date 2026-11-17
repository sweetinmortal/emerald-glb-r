# Offline vanilla preparation

The existing repack is based on RamDll 2.20 and includes MindTheGapps. The first standalone preparation step identifies the Google apps and GMS APEX in the verified product and system_ext PAX archives. The system archive and the WFOMIXM hardware partitions are outside this filter's scope.

Run the inventory with Python 3.10 or newer. Supply the product-clean-input.pax.tar and system-ext-clean-input.pax.tar produced by the original verified repack pipeline.

```sh
python scripts/degoogle.py --dry-run \
  --product-tar /path/to/product-clean-input.pax.tar \
  --system-ext-tar /path/to/system-ext-clean-input.pax.tar
```

The default plan removes 41 archive members containing 689,181,402 bytes from the tested inputs. This count includes directories. The JSON records source archive hashes, the manifest hash, individual removal paths and the approval digest. TalkBack and the dialer-support library are retained by default. Google Sans and its overlay are retained because the font configuration references that font in 72 places.

Some XML files contain permissions for both Google and retained Android components. In particular, the Google-named system_ext permission file also grants emergency-app privileges. The filter retains those mixed files. A future targeted rewrite would need its own review. The AOSP keyboard, its existing JNI libraries, WebView and LineageSetupWizard are retained.

After reviewing the complete plan, use its plan_sha256 value to create new filtered copies. The output directory must not already exist.

```sh
python scripts/degoogle.py --apply \
  --product-tar /path/to/product-clean-input.pax.tar \
  --system-ext-tar /path/to/system-ext-clean-input.pax.tar \
  --approved-plan APPROVED_PLAN_SHA256 \
  --output /path/to/new-vanilla-stage
```

The optional flags --remove-talkback and --remove-dialer-support change the plan and its approval digest. Removing dialer support also requires a dependency audit before an image is built. Font removal is not implemented.

The filter verifies retained file contents, archive metadata, links and PAX attributes. A successful filter report covers the copied archives. The full preparation pipeline combines EROFS reconstruction, regenerated AVB descriptors, OTA signing and package verification, followed by an initial-setup test on the phone.

On 2026-11-15 the default plan was applied to fresh copies. Both EROFS images passed filesystem checks and a complete read-only export comparison against the filtered archives. Product contains 609 retained entries and is 373,563,392 bytes. System_ext contains 3,618 retained entries and is 275,206,144 bytes. Retained file contents, owners, modes, modification times, links and extended attributes match. These are unsigned filesystem images at this stage.

The [filesystem verification record](vanilla-filesystems-20261115.json) includes the image and tool hashes, archive input hashes and approval digest.

On 2026-11-16 the AVB chain and full OTA were signed and verified, and the ZIP was exported with a matching SHA-256. The [sanitized OTA verification record](vanilla-ota-verification-20261116.json) covers all 14 reconstructed partition hashes, 11 excluded firmware partitions, ZIP signature, explicit native payload and metadata signature checks, and the exact 41 retained APEX package versions. The GMS APEX is absent. The vendor charging-control patch is preserved.

The candidate filename is lineage-24.0-emerald-glb_r-WFOMIXM-VANILLA-HEALTH-EXPERIMENTAL.zip. It contains 2,302,608,962 bytes, about 2.14 GiB. Its SHA-256 is `40f02607109901981b1b2f1e1747abd4d2998f80501835476598dd6de664f9f1`. This exceeds GitHub's per-asset release limit of under 2 GiB. Binary distribution remains a separate step. [GitHub release limits](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases#storage-and-bandwidth-quotas)

On 2026-11-16 the candidate booted as a DSU guest. Android reported boot complete, device provisioned and user setup complete; Launcher3 was active, and the guest had a separate 8 GiB `userdata_gsi`. No major GApps or GMS were observed; TalkBack and Google Sans remained. The verification record is [sanitized and portable](vanilla-dsu-verification-20261117.json). It omits host paths, serials, IP addresses, process IDs, raw crash output, keys and user data.

The current metadata preparer stages APEX packages from cached donor archives. Before reusing it for vanilla, rebuild the target-files APEX trees from the filtered inputs. add_img_to_target_files reads those trees to generate apex_info.pb. Running it against the old donor tree would keep the removed GMS APEX in the metadata. Verify that the resulting APEX list matches the actual images and contains no com.google.android.gmssystem entry.

The tested charging-control addition lives in the patched vendor image. Excluding vendor from a future payload would require the recipient to already have that matching patched vendor. The first vanilla preparation retains this dependency explicitly. The owner's 2026-11-17 confirmation says the DSU guest's Quick Settings QR tile opened a scanner. The baseline product inputs include an exported Aperture `QrScannerActivity` and an overlay default pointing to it. `DeviceConfig` and the secure QR component setting both read `null` in the guest; that does not establish that a scanner is missing. The record captures the APK hashes and the confirmation.

Root was present during the owner's runtime charging tests. The candidate OTA uses the clean `vendor_boot` from the charging-control baseline. The DSU boot ran on the host's existing kernel and Magisk-patched `vendor_boot`, so it does not verify booting the candidate's clean `vendor_boot`, a new vbmeta root, or another device. Magisk integration for a subsequent installation is a separate step.

The DSU userspace boot completed setup, but a full OTA boot and hardware validation remain untested; the candidate is not ready for general flashing. One Dolby boot receiver crash was observed before credential-encrypted storage became available. A [source patch](../patches/dolby/README.md) and unsigned review candidate were prepared and statically reviewed; they are not integrated in this candidate or tested on Android. The patch also documents its process-lifetime limitation and the original shared-UID signing requirement. That single early-boot event does not establish that Dolby is wholly broken. The working installation's other test results apply to the original GApps repack and the later charging-control update.
