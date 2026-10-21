# Handoff - local/external workflow reconciliation

- **Date:** 2026-09-20
- **Project:** CoOOH/Al OER Spin Mechanism
- **Workflow:** `research-project-workflow` 1.2.0
- **Branch:** `workflow/adopt-local-first-v1.2`
- **Scope:** local and remote read-only inventory; no new calculation

## Verified

- The historical local execution/data workspace is non-Git.
- A separate Git checkout/worktree is used for canonical durable-state synchronization.
- The remote compute environment was verified through a machine-local safe SSH runner; endpoint/user/home-path details remain outside public Git.
- External compute/data families are indexed with logical aliases and relative namespaces in the three manifests.
- Package validators passed during reconciliation as recorded in the project records.

## Workspace rule

The legacy local directory is an execution/data workspace, not a second source of project truth. Cross-device-relevant changes must be reconciled into the canonical Git workspace before closeout.

## Conflicts retained

- One remote reaction-density final-directory mapping does not yet match the legacy local packaged provenance.
- Historical remote analysis lifecycle labels must not overwrite package-level validation state.

## Next action

Review PR #1. Resolve state conflicts only when required by downstream work. Do not merge automatically.
