# Workflow adoption checklist

- [x] Read project-specific AGENTS instructions.
- [x] Run `project_doctor.py` before reconciliation.
- [x] Confirm global workflow Skill version `1.2.0`.
- [x] Verify the active local path and detect that it is not a Git checkout.
- [x] Verify the separate staging Git mirror and preserve its clean state.
- [x] Inspect `.gitignore`; no new ignore rule was added.
- [x] Inventory local compact, derivative, and large-only assets.
- [x] Inspect remote CP2K/cDFT/VASP/LOBSTER/PDOS/Bader/reaction-density roots read-only.
- [x] Update front-door manifests without copying raw data.
- [x] Create a durable handoff and migration report.
- [x] Record reaction-density and historical-manifest conflicts explicitly.
- [x] Review credentials and large-file risk; no credential was added.
- [ ] Resolve the remote-final versus local-artifact reaction-density conflict.
- [ ] Review PR #1 and decide whether to merge; this audit does not merge it.

