# Workflow adoption report

- **Date:** 2026-09-20
- **Workflow contract:** 1.2.0
- **Repository:** `wishion-Ni/CoOOH_Al_OER_spin_mechanism`
- **Base commit:** `9486c417f7f6dfefa03fca234a6442738e022f93`

## Adoption model

This is a mature established repository. The workflow is therefore installed as a root-level **interface/adapter layer**, not as a replacement project structure.

## Existing canonical architecture preserved

- `PROJECT_MEMORY.md`
- `README.md`
- `00_project_management/`
- `01_experimental_constraints/`
- `02_DFT_CP2K/`
- `03_cDFT/`
- `04_VASP_analysis/`
- `05_analysis_scripts/`
- `manuscript/`
- archive/provenance directories
- existing GitHub Actions and scripts

## New workflow interface

- `AGENTS.md`
- `PROJECT.md`
- `STATUS.md`
- `TASKS.md`
- `DECISIONS.md`
- `DATA_MANIFEST.md`
- `COMPUTE_MANIFEST.md`
- `SERVER_MANIFEST.md`
- `WORKFLOW_VERSION`
- bootstrap/migration prompts
- durable handoff directories

## Safety

- no existing scientific/project-native file was overwritten in this pass;
- no external path was invented;
- no large raw calculation data were added;
- no credentials were added;
- no new calculation was launched.

## Remaining requirement

Local Codex must verify the actual local/external environment before this adoption is considered complete.
