# STATUS

## Current phase

`LOCAL_EXTERNAL_RECONCILIATION / COMPLETE_WITH_REVIEW`

## Verified workflow snapshot

- Global workflow Skill: `research-project-workflow` `1.2.0`.
- Workflow/project contract: current at `1.2.0`.
- Canonical durable-state workspace: GitHub repository plus local Git checkout/worktree.
- Legacy execution/data workspace: verified non-Git historical project directory; exact machine-local path is intentionally not stored in this public repository.
- Reconciliation branch: `workflow/adopt-local-first-v1.2`; PR #1 remains open and draft.
- Remote compute environment: verified read-only through the configured local safe SSH runner; connection endpoint and credentials remain in local configuration rather than Git.

## Reconciliation state

- Existing project-native scientific/project-management records remain canonical.
- External compute/data roots were inventoried and mapped into the front-door manifests without copying large raw data into Git.
- Package validators were executed successfully during reconciliation and recorded in the project-native/reconciliation records.
- No new calculation or scheduler operation was launched or altered.
- The workflow now has an explicit split-workspace rule: execution may occur in the legacy local workspace, but durable cross-device state must be written back to the canonical Git workspace.

## Review boundaries

- **STATE CONFLICT TO REVIEW:** one reaction-density final-directory mapping is not yet provenance-consistent across remote and local packaged artifacts.
- **STATE CONFLICT TO REVIEW:** a historical remote analysis manifest and the current compact package use different lifecycle labels; package-specific validation/provenance must control promotion.
- Active scheduler jobs observed during inventory were not modified or assumed to belong to the current publication package.
- No scientific conclusion was changed during workflow adoption.

## Merge readiness

Workflow reconciliation is complete enough for review. Merge remains blocked only on reviewer/user acceptance of the recorded state conflicts and the split-workspace policy; no infrastructure reconfiguration is required.
