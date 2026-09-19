# DECISIONS

## D-001 - Repository state is canonical

Reconstruct state from versioned records plus verified local/server assets, not from chat history alone.

## D-002 - Preserve the mature project structure

The workflow layer is an interface/adapter. Existing scientific records, packages, archives, and labels remain authoritative.

## D-003 - Large/raw compute assets stay external

Git stores compact source data, scripts, validated derivatives, manifests, and provenance. Full raw calculation/data trees remain in the legacy local or remote source workspaces unless explicitly requested.

## D-004 - Split workspace is intentional

The historical local execution/data workspace is non-Git and is not silently converted. The GitHub repository plus a local Git checkout/worktree is the canonical durable-state workspace. Neither workspace is overwritten, reset, cleaned, or merged automatically during reconciliation.

## D-005 - Conflicting provenance is explicit

The remote final reaction-density directory, the legacy local packaged artifact, and historical manifests are not silently collapsed into one status. Any mismatch is recorded as `STATE CONFLICT TO REVIEW` until source identity is rechecked.

## D-006 - No new science during adoption

No VASP, CP2K, cDFT, LOBSTER, Bader, scheduler, or other calculation is launched or altered solely for workflow adoption.
