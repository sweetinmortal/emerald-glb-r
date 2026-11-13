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

- Fork `emerald-lineage/android_device_xiaomi_emerald`.
- Push the `glb_r-wfomixm` branch.
- Open a draft PR referencing issue #1.
- Adjust or split the PR if the maintainer asks.

## M3 — Second-device validation

- Reproduce the install on another Redmi Note 14S of the same model.
- Compare build properties, SELinux state, and basic hardware tests.
- Record any differences.

## M4 — Distribution decision

- Review which binaries can be redistributed.
- Keep the current 2.33 GiB ZIP out of GitHub Releases.
- Use external hosting or split artifacts only if the licensing is clear.

## M5 — Longer soak test

- Calls and SMS
- Camera and video recording
- Charging and battery behavior
- Suspend/idle drain
- Bluetooth and Wi-Fi stability
- OTA/update behavior

## M6 — Upstream merge or standalone home

- If upstream accepts the changes, link the merged commits here.
- If not, keep this repository as the clearly marked unofficial home for the variant.
