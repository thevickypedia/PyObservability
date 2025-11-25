Release Notes
=============

v0.0.0a2 (11/25/2025)
---------------------
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

v0.0.0a1 (11/24/2025)
---------------------
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
