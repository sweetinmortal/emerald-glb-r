# Upstream status

- **Issue:** [#1 — Redmi Note 14S global (2502FRA65G / glb_r) tested on WFOMIXM](https://github.com/emerald-lineage/android_device_xiaomi_emerald/issues/1)
- **Opened:** 2026-11-09
- **Response:** none at the last check recorded by OpenCode on 2026-11-15

## Planned contribution

- Fork: `sweetinmortal/android_device_xiaomi_emerald`
- Branch: `glb_r-wfomixm`
- Draft PR title: `emerald: add glb_r / WFOMIXM variant support`
- Scope: minimal VINTF matrix, mount-policy adjustments, and configuration changes needed for `glb_r`; no binaries.

## Current direction

On 2026-11-15 the device owner chose to continue the standalone community
contribution here. The removal tool, reviewed plan and filtered archive copies
were completed, followed by EROFS, AVB and OTA verification. A separate DSU
guest completed setup, and the owner confirmed its Quick Settings QR reader.
The contribution preserves the WFOMIXM hardware base and charging-control work.

The next publication stages are the source/documentation repository and a
SourceForge project for eventual binary downloads. The complete OTA install
procedure, compatibility patch series, portable packaging workflow and binary
redistribution review remain pending. See [publication status](publication.md).

The [WFOMIXM source-port review](source-port-readiness.md) records the
305/306 kernel and image differences and the validation still needed for
a formal LineageOS submission.

The existing issue remains a reference. Preparation of the standalone tooling can proceed independently of a maintainer response. The draft PR described above remains a possible future contribution.
