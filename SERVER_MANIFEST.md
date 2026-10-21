# SERVER MANIFEST

Non-secret environment map. Passwords, tokens, private keys, connection endpoints, usernames, machine-local absolute paths and credential-helper paths are intentionally excluded from this public repository.

### REMOTE-COMPUTE-01

- **Connection:** resolved through the configured machine-local safe SSH runner
- **Project namespace:** `sfs/CoOH/`
- **Scheduler observed:** Slurm
- **Allowed operation during reconciliation:** read-only inventory only
- **Last verified:** 2026-09-20

### LOCAL-LEGACY-01

- **Role:** legacy execution/data workspace
- **Git state:** non-Git historical directory
- **Exact machine-local path:** intentionally omitted from public Git
- **Large local-only assets:** indexed through `DATA_MANIFEST.md`
- **Canonical-state rule:** this workspace is not project memory; durable updates must be reconciled into the canonical Git workspace
- **Last verified:** 2026-09-20

### LOCAL-GIT-01

- **Role:** canonical local Git checkout/worktree for durable-state synchronization
- **Exact machine-local path:** intentionally omitted from public Git
- **Remote:** `wishion-Ni/CoOOH_Al_OER_spin_mechanism`
- **Workflow branch during adoption:** `workflow/adopt-local-first-v1.2`
- **Canonical branch after accepted merge:** `main`

## Scheduler caution

Jobs observed during the read-only inventory were not submitted, canceled, suspended or modified by workflow reconciliation.
