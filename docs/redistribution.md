# Binary provenance and redistribution

The [local stock-input tool](stock-kernel-inputs.md) is available as source.
The experimental OTA stays local while its redistribution and recovery-install
checks are pending. The checks below cover the candidate with SHA-256
`40f02607109901981b1b2f1e1747abd4d2998f80501835476598dd6de664f9f1`.

## Kernel and modules

- The stock kernel identifies itself as
  `6.12.30-android16-5-g6e872b4863d6-ab13847919-4k`. The Android GKI tag
  `android16-6.12-2025-07_r7` identifies the matching commit and Android CI
  build `13847919`. The local tool pins the kernel bytes extracted from Xiaomi's
  OTA. Independent comparison with the original CI binary remains unverified.
  [AOSP GKI tag](https://android.googlesource.com/kernel/common/+/refs/tags/android16-6.12-2025-07_r7).
- The stock bundle has 490 module files across the platform ramdisk,
  `system_dlkm` and `vendor_dlkm`, representing 480 distinct hashes.
  Of those files, 82 declare the GKI build release and 408 declare one of two
  other build releases. The shipped `fpsgo.ko` and `perf_common_v.ko`
  in `vendor_dlkm` declare `Proprietary` in their module metadata.
  The module tags do not establish a redistribution grant or the complete
  corresponding source.
- Xiaomi's published `emerald_r-u-oss` kernel tree identifies itself as Linux
  5.10.209. The matching OEM source and build material for this 6.12 module set
  remain unverified. [Xiaomi kernel Makefile](https://github.com/MiCode/Xiaomi_Kernel_OpenSource/blob/b183d9cceaeb4329781b597e4b520ea6a2687c7a/Makefile).

## Other bundled binaries

- The 14-partition payload still includes vendor components. Its vendor tree
  contains Widevine and OEMCrypto as well as Dolby libraries. The candidate
  retains the donor's signed Dolby APK. Redistribution coverage for these
  binaries remains unverified. The source patch published in this project
  covers its own changes. [Widevine overview](https://developers.google.com/widevine/drm/overview).
- The Google-app removal filter retains the TalkBack APK for accessibility
  and leaves the dialer support JAR and Google LatinIME libraries in the
  image. The included binaries' exact source and redistribution terms remain
  unverified. [TalkBack source](https://github.com/google/talkback).
- The bundled Google Sans Flex font identifies itself as version
  `3.007;[58cd9cb9b]` and declares SIL Open Font License 1.1 in its metadata.
  Its SHA-256 differs from the Android font in the upstream v3.007 download.
  Retain the applicable license and notices when redistributing an approved font.
  [Upstream release](https://github.com/googlefonts/googlesans-flex/releases/tag/v3.007),
  [OFL text](https://github.com/googlefonts/googlesans-flex/blob/58cd9cb9b/OFL.txt).

Xiaomi's operating system agreement covers the embedded files and updates,
preserves the licenses that apply to open-source components, and restricts
publication of its proprietary software. The stock vendor notices reviewed
do not establish a grant for including the Widevine APEX or OEMCrypto in
this OTA. [Xiaomi operating system agreement, sections 1, 2 and 6](https://terms.miui.com/doc/eula/en_US.html).

A binary release needs a complete source, license and notice inventory for the
actual bytes being shared. SourceForge's upload terms require sufficient rights
to distribute third-party content. [SourceForge terms](https://slashdotmedia.com/terms-of-use/).
