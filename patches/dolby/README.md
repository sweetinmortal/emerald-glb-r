# Dolby preset migration after user unlock

This source patch addresses the first-boot receiver crash observed in the
vanilla DSU test. The `BOOT_COMPLETED` handler accessed credential-encrypted
preferences before that user's storage was available. The separate
`LOCKED_BOOT_COMPLETED` path already restores device-encrypted settings and
stays unchanged.

The patch checks `UserManager.isUserUnlocked`, registers an application-context
receiver for `ACTION_USER_UNLOCKED` when needed, and checks again after
registration to cover that race. It preserves the original migration and its
success marker. The synchronized callback unregisters itself after handling.

Base: [AOSPA/android_hardware_xiaomi at
1a3e75d36079e8ba9d1b324acdf5201157a307a6](https://github.com/AOSPA/android_hardware_xiaomi/tree/1a3e75d36079e8ba9d1b324acdf5201157a307a6).
Apply [the patch](dolby-unlock-migration-source.patch) to that source tree after
running `git apply --check`. [Provenance and verification](provenance.json)
record its hashes and test boundary. The patch follows the upstream Apache-2.0
license.

Offline review confirmed that the patch applies to that commit. A corresponding
smali candidate assembled successfully: only the existing `onBootCompleted`
method changes, three helper methods are added, and 1,910 other ZIP payloads,
including the manifest, stay byte-identical. This does not establish a successful
Kotlin platform build or an Android runtime test.

The dynamic receiver depends on the process surviving until unlock. If that
process dies first, migration can remain pending until a later controller
entry or boot. This limitation needs runtime validation.

The patch is **not integrated into the vanilla OTA**. The original Dolby APK
uses `android.uid.system` and the donor's platform certificate. The locally
assembled APK is unsigned and is excluded from this repository. A compatible
signer/platform signing chain is required before replacing that shared-UID
package; an OTA or AVB signing key does not provide that compatibility. See
[Android app signing](https://source.android.com/docs/security/features/apksigning).

No APK, private signing material or device data is provided here. The existing
ROM keeps its original signed Dolby APK.
