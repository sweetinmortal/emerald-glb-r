# Scripts

No scripts are published yet.

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
