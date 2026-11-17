# Scripts

The local vanilla preparation adds degoogle.py and manifest.json. The tool prints a removal plan by default. Applying a reviewed plan creates fresh PAX copies and verifies the retained contents and metadata. See [the vanilla preparation procedure](../docs/vanilla.md).

Supply both archive paths with `--product-tar` and `--system-ext-tar` when using
this repository. The manifest retains the historical relative input locations
for provenance; it does not download or create those archives. Those defaults
are resolved from this repository root, without assuming a particular checkout
depth on the computer.

The plan is to publish sanitized versions of the packaging and verification helpers used for the test:

- input hash verification;
- AVB chain verification;
- target-files staging;
- OTA packaging;
- OTA verification.

Before publication, the scripts must be cleaned of:

- local Windows paths and usernames;
- private keys and certificates;
- stock firmware and vendor images;
- build artifacts and caches;
- personal or device-identifying logs.

The scripts will be documented and tested from a clean checkout before they are added here.
