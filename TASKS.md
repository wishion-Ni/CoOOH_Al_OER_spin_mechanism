# TASKS

Cross-session workflow queue. Scientific work remains in the project-native records.

| ID | Priority | Task | Status | Evidence |
|---|---:|---|---|---|
| W-001 | P0 | Verify active local execution workspace and Git state | DONE WITH REVIEW | legacy workspace verified non-Git; canonical Git workspace handled separately |
| W-002 | P0 | Inventory local-only assets before changing data/ignore policy | DONE WITH REVIEW | local package/size inventory completed |
| W-003 | P0 | Inventory external compute roots and map packages | DONE WITH REVIEW | read-only remote audit and manifests |
| W-004 | P0 | Confirm workflow Skill/project version | DONE | doctor + `WORKFLOW_VERSION` |
| W-005 | P1 | Reconcile front-door manifests with native records | DONE WITH REVIEW | DATA/COMPUTE/SERVER manifests; conflicts retained |
| W-006 | P1 | Create post-reconciliation handoff | DONE | `.agent/handoffs/2026-09-20_local-reconciliation.md` |
| W-007 | P1 | Review secrets, large files and synchronization diff | DONE WITH REVIEW | no credentials/raw large data added |
| W-008 | P1 | Define canonical Git workspace versus legacy execution workspace | DONE | split-workspace policy recorded in `PROJECT.md` |
| W-009 | P1 | Resolve recorded provenance/state conflicts when needed | OPEN | explicit `STATE CONFLICT TO REVIEW` records |
| W-010 | P1 | Merge workflow adoption PR | BLOCKED | user/reviewer decision; PR remains draft |

## Session rule

Work may be executed against the legacy local workspace or remote compute roots, but any durable cross-device state change must be reconciled into the canonical Git workspace before closeout.
