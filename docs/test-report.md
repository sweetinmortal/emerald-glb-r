# Test report — 2026-11-08

## Device

| Property | Value |
|---|---|
| Device | Redmi Note 14S global |
| Model | `2502FRA65G` |
| Variant | `emerald_r_global` |
| SKU | `glb_r` |
| SoC | `mt6789` |
| Stock base | `OS3.0.306.0.WFOMIXM` |
| Slot tested | `_b` |
| SELinux | `Enforcing` |

## Build

| Property | Value |
|---|---|
| Build | `LineageOS 24.0-20261106-UNOFFICIAL-emerald` |
| `ro.lineage.version` | `24.0-20261106-UNOFFICIAL-emerald` |
| `ro.lineage.releasetype` | `UNOFFICIAL` |
| `ro.build.display.id` | `CP2A.260605.016` |
| `ro.build.version.release` | `17` |
| `ro.build.version.sdk` | `37` |
| `ro.build.version.security_patch` | `2026-10-05` |
| `ro.build.date` | `Sat Nov  7 00:55:00 MSK 2026` |
| `ro.build.type` | `user` |
| `ro.build.tags` | `release-keys` |
| `ro.build.flavor` | `lineage_emerald-userdebug` |
| Kernel | `6.12.30-android16-5-g6e872b4863d6-ab13847919-4k` |
| `ro.odm.build.version.incremental` | `OS3.0.306.0.WFOMIXM` |

Build fingerprint:

```text
Redmi/emerald_r_global/emerald:16/BP2A.250605.031.A3/OS3.0.305.0.WNFMIXM:user/release-keys
```

The fingerprint carries the donor's `WNFMIXM` string because the donor system runs over the stock vendor. The actual vendor/ODM incremental is `OS3.0.306.0.WFOMIXM`.

## Checklist

| Test | Result |
|---|---|
| Clean install from stock `OS3.0.306.0.WFOMIXM` | Pass |
| First boot from slot B | Pass |
| Second consecutive boot from slot B | Pass |
| SELinux `Enforcing` | Pass |
| LTE / IMS | Pass |
| Wi-Fi hotspot | Pass |
| Second device of the same model | Pending |
| Long soak (calls, camera, video, charging, suspend) | Pending |

## Limitations

- One device only.
- No IMEI, serial number, account data, or personal identifiers are recorded here.
- The test does not prove compatibility with other variants, bases, or hardware revisions.

## Follow-up OTA with Google apps — 2026-11-13

The charging-control OTA upgraded the existing LineageOS installation from
slot B to slot A on the same Redmi Note 14S and WFOMIXM base. It retained the
donor's Google apps. Recovery sideload finished without formatting or clearing
userdata. Android booted in slot A and the charging-control service and its
Settings screen were verified. App-by-app data and account-session retention
were not independently verified during this run.

The tested ZIP has SHA-256
`39f0ac044f1ae91c0161a28e0deec2ff814b76f55d50260bea1b67ba6b41e842`.

On 2026-11-18, all eight logical partition hashes on the running device
matched this OTA. The GMS APEX, Play Store and Google Services Framework
also matched the separate MindTheGapps release byte for byte.
[MindTheGapps 17 ARM64 release](https://github.com/MindTheGapps/17.0.0-arm64/releases/tag/MindTheGapps-17.0.0-arm64-20261022_132445).

Four Google overlays had different resource contents and signing certificates,
so this comparison does not establish direct add-on compatibility. The
[vanilla test](vanilla.md) used DSU with separate data. Full installation of
the vanilla ZIP remains untested.
