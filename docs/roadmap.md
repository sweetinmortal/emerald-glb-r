# Roadmap

## M0 — Documented test (current)

- Publish the compatibility notes and test report.
- Keep the exact build and device properties.
- Link the upstream issue.

## M1 — Minimal patch series

- Consolidate only the changes required for `glb_r` / WFOMIXM.
- Keep the VINTF matrix and mount-policy changes separate.
- Include commit messages and verification notes.
- Do not include firmware, GApps, images, or signing keys.

## M2 — Upstream review

The issue is open. On 2026-11-15 the device owner chose the standalone preparation path. The immediate work is the offline vanilla repack tooling. A future upstream PR can reuse the reviewed compatibility changes.

## M3 — Second-device validation

- Reproduce the install on another Redmi Note 14S of the same model.
- Compare build properties, SELinux state, and basic hardware tests.
- Record any differences.

## M4 — Distribution decision

- Prepare a default dry run that identifies the exact Google-app removal scope.
- Apply an approved plan to fresh copies of the product and system_ext PAX archives.
- Verify retained contents, permissions, ownership, links and extended attributes.
- Rebuild EROFS, regenerate APEX metadata, regenerate AVB descriptors and sign a separate OTA.
- Test the initial setup with LineageSetupWizard in a clean full OTA installation before describing full OTA and hardware validation as complete. The 2026-11-16 DSU guest did reach device provisioned and user setup complete.
- Review which binaries can be redistributed.
- The 2026-11-16 vanilla candidate passed AVB, ZIP and payload signatures, full 14-partition replay and exact APEX metadata checks. Its exported size is 2,302,608,962 bytes (about 2.14 GiB). DSU userspace boot and setup were verified, and the owner confirmed the Quick Settings QR tile worked on 2026-11-17. A full OTA boot and hardware test remain pending; it is not ready for general flashing. See the [sanitized DSU verification record](vanilla-dsu-verification-20261117.json).
- Keep the current 2.14 GiB ZIP out of GitHub Releases.
- Use external hosting or split artifacts only if the licensing is clear.

## M5 — Longer soak test

- Calls and SMS
- Camera and video recording
- Charging and battery behavior
- Suspend/idle drain
- Bluetooth and Wi-Fi stability
- OTA/update behavior

The charging-control update has been tested on slot A with SELinux enforcing and the configured 80 percent cutoff observed. The thermal investigation remains open. Raw charge_control_limit values are mitigation levels. They do not represent amperes. The vanilla baseline includes the exported Aperture QR activity and its default overlay; the owner confirmed the Quick Settings tile worked in the DSU guest. `DeviceConfig` and the secure component setting were `null` there, which does not imply a missing scanner. A single Dolby receiver crash was observed before credential-encrypted storage was available; the [reviewed source patch](../patches/dolby/README.md) remains separate from the candidate, pending compatible signing and runtime validation.

## M6 — Upstream merge or standalone home

- If upstream accepts the changes, link the merged commits here.
- If not, keep this repository as the clearly marked unofficial home for the variant.
