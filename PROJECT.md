# PROJECT

## Identity

- **Project name:** CoOOH/Al OER Spin Mechanism
- **Slug:** `coooh-al-oer-spin-mechanism`
- **Repository:** `wishion-Ni/CoOOH_Al_OER_spin_mechanism`
- **Workflow version:** `1.2.0`
- **Canonical branch:** `main`
- **Reconciliation branch:** `workflow/adopt-local-first-v1.2`

## Workspace model

This project intentionally uses two different workspace roles:

1. **Canonical durable-state workspace:** the GitHub repository and a local Git checkout/worktree. Versioned workflow state, manifests, scripts, project-native records and handoffs belong here.
2. **Legacy execution/data workspace:** the established non-Git local project directory used for historical local artifacts and execution. It is treated as an external workspace/data root, not as a second canonical project memory.

The exact machine-local path of the legacy workspace is intentionally kept out of the public repository. Local Codex may resolve it from machine-local context.

Any cross-device-relevant change discovered while working in the legacy workspace must be reconciled back into the canonical Git workspace before session closeout.

## Objective

Maintain reproducible, auditable computational evidence for the CoOOH/Al OER spin mechanism and prepare compact manuscript-ready packages without making chat history or a machine-local directory the source of truth.

## Canonical scientific records

The mature project-native records are versioned in the Git repository under `PROJECT_MEMORY.md`, `00_project_management/`, `01_experimental_constraints/`, `02_DFT_CP2K/`, `03_cDFT/`, `04_VASP_analysis/`, `05_analysis_scripts/`, and `manuscript/`.

The workflow layer does not replace those records or promote archived, diagnostic, preliminary, superseded, or incomplete assets.

## Adoption boundary

This reconciliation indexes verified local and server assets only. It does not start or alter VASP, CP2K, cDFT, LOBSTER, scheduler, or other calculations, and it does not upload large raw calculation trees.
