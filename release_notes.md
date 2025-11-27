Release Notes
=============

v0.1.0 (11/27/2025)
-------------------
- [a6c08cb](https://github.com/thevickypedia/PyObservability/commit/a6c08cbd3c83080dd6a1ae6281c9da41873d707f) chore: Release ``v0.1.0``
- [5b90baf](https://github.com/thevickypedia/PyObservability/commit/5b90baf4ee3e0bbd54eb693fcc87b61af344f497) chore: Log payload generated time
- [4ea1e0a](https://github.com/thevickypedia/PyObservability/commit/4ea1e0a3bad0ad3bb340d9e9c48ffdd753b1fbc5) style: Improve service level metrics' display
- [9fa9c7f](https://github.com/thevickypedia/PyObservability/commit/9fa9c7fdc51336723e52240037a62a5f7e306cf7) feat: Include a reconnect loop around fetch metrics
- [85e5456](https://github.com/thevickypedia/PyObservability/commit/85e545622529594b885ae24dfc22ffee2cf14b12) perf: Handle streaming response from the server without making redundant API calls
- [e0f4a46](https://github.com/thevickypedia/PyObservability/commit/e0f4a46d66ed6e82f636c1ac4fafe9d03dec77be) perf: Auto-generate table headers for disks, pyduisk, and certificates
- [e30d3c5](https://github.com/thevickypedia/PyObservability/commit/e30d3c565190bc375cc6a030bd50663f32750c71) lint: Make linter happy
- [ea7e4cf](https://github.com/thevickypedia/PyObservability/commit/ea7e4cfeda082364d29ab2af248aa49faad9c548) style: Display certificates' information in a table
- [6551091](https://github.com/thevickypedia/PyObservability/commit/65510912c1fc50ad24ad93cc744d55a8c41dd544) perf: Create all coroutines in a list and run them concurrently
- [43d0a86](https://github.com/thevickypedia/PyObservability/commit/43d0a86489c01484e3c526a9a7d93ec7dd3c1767) style: Group individual elements for system, ip, and processor info to one meta tag
- [f49f7ed](https://github.com/thevickypedia/PyObservability/commit/f49f7edbeab41f93c57121b59dee81c24f335d1f) style: Make all meta cards consistent
- [82bdaf5](https://github.com/thevickypedia/PyObservability/commit/82bdaf59ec8ea1405ed98269d364bc563c950598) style: Add pretext for CPU and GPU names
- [b715a75](https://github.com/thevickypedia/PyObservability/commit/b715a757f146261cd47087543e605cb80bbe54b7) style: Avoid cluttering at the top row of the UI
- [062f19d](https://github.com/thevickypedia/PyObservability/commit/062f19dc23dc115ec3c4aa8f18077c327213814a) refactor: Remove unnecessary ``||`` in disk metrics
- [4651ac5](https://github.com/thevickypedia/PyObservability/commit/4651ac518f0877667764bb820976b43d950b5916) feat: Update UI to include all information sent by the API
- [f8f8aea](https://github.com/thevickypedia/PyObservability/commit/f8f8aea1e181a9be65c1f8b179529d794423f347) refactor: Simplify individual API calls with a single entrypoint to get system resources as a ``StreamingResponse``
- [045fb48](https://github.com/thevickypedia/PyObservability/commit/045fb4859dcb9994cbe4ab2aa07b87089a2f1e93) chore: Update release notes for v0.0.3

v0.0.3 (11/25/2025)
-------------------
- [24a15bf](https://github.com/thevickypedia/PyObservability/commit/24a15bfd9bee2cfa5024997a66c2d3e2d1b20eb7) chore: Release ``v0.0.3``
- [546be8d](https://github.com/thevickypedia/PyObservability/commit/546be8d80edf00211a09a042eb4d39cca247c7f7) refactor: Move "NO DATA" propagation to the UI instead of rendering it from the API
- [7448b3d](https://github.com/thevickypedia/PyObservability/commit/7448b3dd240b445273472b89b4870588a113247e) chore: Update release notes for v0.0.2

v0.0.2 (11/25/2025)
-------------------
- [8a98ac1](https://github.com/thevickypedia/PyObservability/commit/8a98ac12547f882cb9e54821c3c0589e4aee1d28) chore: Release ``v0.0.2``
- [f1c43c9](https://github.com/thevickypedia/PyObservability/commit/f1c43c9bd1702d855e9b5a0c0d4213b66305112e) fix: Avoid potential attribute errors
- [9f8120c](https://github.com/thevickypedia/PyObservability/commit/9f8120c1fcb3bef8be254414048ceffeb1692502) perf: Improve alias choices
- [f40d302](https://github.com/thevickypedia/PyObservability/commit/f40d30208b3991029babe8b0daea42501a181636) chore: Update release notes for v0.0.1

v0.0.1 (11/25/2025)
-------------------
- [8b0f494](https://github.com/thevickypedia/PyObservability/commit/8b0f4940042050830db026228725d959f8a75b8d) chore: Release ``v0.0.1``
- [15d2720](https://github.com/thevickypedia/PyObservability/commit/15d2720b9bd9e1b9aaaae975cba885a283159f7c) docs: Update README.md
- [217aa5a](https://github.com/thevickypedia/PyObservability/commit/217aa5a95d7c88aafaca1e5fda7391cb898b4792) feat: Make env vars accept alias choices
- [bf831db](https://github.com/thevickypedia/PyObservability/commit/bf831db0dab4cfe36da2774e52c712c03905122c) revert: Default factory for pydantic env config
- [fd43528](https://github.com/thevickypedia/PyObservability/commit/fd435287196067dbfea4844a856387e0ba790944) feat: Make env vars case in-sensitive along with multiple options
- [3208d29](https://github.com/thevickypedia/PyObservability/commit/3208d2934ebedd8269b139ddf864c4291ba76c31) feat: Improve security for observability hosting with UI auth
- [5786768](https://github.com/thevickypedia/PyObservability/commit/5786768e3a086727fecf9fceca55af1652fa14bf) chore: Update release notes for v0.0.0a2
- [8d12f2e](https://github.com/thevickypedia/PyObservability/commit/8d12f2e5c3ad6aca290e5123480b23f30608ad6a) chore: Release ``v0.0.0a2``
- [dac0fdf](https://github.com/thevickypedia/PyObservability/commit/dac0fdf78e22755bc696cd11119b8368ed1bf0cb) fix: Avoid attribute error for env_file open
- [bbc3d26](https://github.com/thevickypedia/PyObservability/commit/bbc3d26916418ee6f59cd1ea7aed65d6462dca28) fix: Fix CLI entrypoint function
- [f2e3c8c](https://github.com/thevickypedia/PyObservability/commit/f2e3c8c7e565651fa60cee8fb93e1fe9622559bd) feat: Enable CLI through pip commands
- [87d328f](https://github.com/thevickypedia/PyObservability/commit/87d328f0e5b154089be759f8a38a2c1e43ea45bd) feat: Create an env loader to support different file types like ``yaml``, ``json`` and plaintext
- [735bc7e](https://github.com/thevickypedia/PyObservability/commit/735bc7eb77969d35675d91bed4edf29c0b54aabd) feat: Include CLI functionality
- [2126e24](https://github.com/thevickypedia/PyObservability/commit/2126e245aa8ef8cba1f34c30eac59dd494d99ea3) refactor: Allow env vars to be sent during instantiation
- [c7fcea5](https://github.com/thevickypedia/PyObservability/commit/c7fcea507f487919742002e587ef26236f926fa6) lint: Run linter
- [f394ed8](https://github.com/thevickypedia/PyObservability/commit/f394ed8b0b3c94a6fac789fac20b8659455b87dd) feat: Onboard ``pydantic`` to load and parse env vars
- [d84e788](https://github.com/thevickypedia/PyObservability/commit/d84e7886bffd1db348a26d29e9515968b0b76598) chore: Update release notes for v0.0.0a1
- [ed65493](https://github.com/thevickypedia/PyObservability/commit/ed654937a9f01de6ffbe2088b0a32ccf6874cb1e) chore: Release ``v0.0.0a1``
- [c06f9eb](https://github.com/thevickypedia/PyObservability/commit/c06f9ebe8c4c54aa488c4e51cc6cfd58400a676e) lint: Add a linter
- [cb303b4](https://github.com/thevickypedia/PyObservability/commit/cb303b4c46198f57a9738b963142a62b8f65af07) style: Remove quoted strings and round off floating values to 2 decimal points
- [7bc6c73](https://github.com/thevickypedia/PyObservability/commit/7bc6c73a33db182e38d9d6e45a85ca81813aa2a2) refactor: Log error messages in the backend instead of rendering it to the UI
- [2467744](https://github.com/thevickypedia/PyObservability/commit/2467744ce0ba29c4ce72f02effd9fb0cbcdace4d) style: Display docker stats as a table
- [b47dc3b](https://github.com/thevickypedia/PyObservability/commit/b47dc3b72443a744f89c142f51e7f81b124ff88c) style: Fix docker and certificate stacks being squeezed to the right
- [765fe62](https://github.com/thevickypedia/PyObservability/commit/765fe62bb78aa6f1420539a721a2baba915b33eb) ci: Add GitHub workflows to automatically upload to pypi, release, and update release notes
- [e44b2a8](https://github.com/thevickypedia/PyObservability/commit/e44b2a851f1bf982e0d91dfda3d79c59bc3aeefd) ci: Add basic ``pypi`` setup
- [ca248c6](https://github.com/thevickypedia/PyObservability/commit/ca248c6a8c83b17528b6bd24e2c7a680e924c682) style: Update UI to start with empty data points and update gradually
- [8d1be7f](https://github.com/thevickypedia/PyObservability/commit/8d1be7ff710e40cbdebb4babf9aa0be75d784958) perf: Stabilize CPU avg chart and improve memory safety in per-core CPU spikelines
- [f4aef70](https://github.com/thevickypedia/PyObservability/commit/f4aef70c28a109503b6ab44d6d35d702bbe20f0e) perf: Avoid overloading browser memory
- [aa45065](https://github.com/thevickypedia/PyObservability/commit/aa45065ff3982c79572cb3e1f7c9462afaf487ea) style: Avoid vertical overflow for CPU sparklines
- [7f7eb2f](https://github.com/thevickypedia/PyObservability/commit/7f7eb2f6d9dd1e758cff75cb211efd35281ce219) feat: Add a base observability page for PyNinja
- [f2aa527](https://github.com/thevickypedia/PyObservability/commit/f2aa527ffe7bd88bd05d2af3006a77a497d2c1a4) Initial commit
