# AGENTS.md

This repository is managed with the global `research-project-workflow` Skill (workflow contract `1.2.0`).

## Operating precedence

1. Explicit user instructions for the current task.
2. This repository's project-specific scientific/technical records.
3. The global `research-project-workflow` Skill.
4. Generic agent defaults.

Chat history is not the authoritative project memory.

## Bootstrap order

For a substantial task, read:

1. `PROJECT.md`
2. `STATUS.md`
3. `TASKS.md`
4. `DECISIONS.md`
5. the task-relevant canonical project records listed below
6. only then inspect additional files or external compute/data locations.

## Canonical project-native records

The workflow front door does not replace the repository's mature internal structure.

- project memory: `PROJECT_MEMORY.md`
- repository map and delivery conventions: `README.md`
- completed-data audit: `00_project_management/FINAL_THEORY_AUDIT_20260917.md`
- detailed result inventory: `00_project_management/THEORY_RESULT_INVENTORY.md`
- unresolved scientific questions: `00_project_management/unresolved_questions.md`
- experimental/theory constraints: `01_experimental_constraints/scientific_constraints.md`
- evidence map: `01_experimental_constraints/evidence_map.md`
- manuscript-facing delivery records: `manuscript/`

When these files define a scientific boundary, preserve it. Do not promote archived, superseded, diagnostic, or preliminary material into current evidence without explicit revalidation.

## Execution model

Local Codex is the default execution layer for:

- local files and applications;
- scripts, tests, plotting and packaging;
- Git/GitHub work;
- SSH/HPC or external compute inspection;
- large-data inventory and compact evidence extraction.

Use ChatGPT selectively for high-level reasoning, architecture, review, literature, or independent critique. Verify consequential advice against the real project files/data before changing durable state.

## Durable state

Update the root workflow files only when the top-level project picture changes:

- `PROJECT.md` — stable identity/scope;
- `STATUS.md` — current verified snapshot;
- `TASKS.md` — cross-project actionable queue;
- `DECISIONS.md` — durable workflow/project-management decisions;
- `DATA_MANIFEST.md` — front-door data index;
- `COMPUTE_MANIFEST.md` — front-door compute index;
- `SERVER_MANIFEST.md` — non-secret external environment map.

Detailed scientific records remain in the existing project-native files.

## Safety and provenance

- Do not store credentials, private keys, tokens, browser sessions, or passwords.
- Do not infer local/server paths from memory.
- Do not upload large raw computational files merely for ChatGPT visibility.
- Distinguish repository-packaged evidence from external raw calculation trees.
- Inspect before rerunning expensive calculations.
- Do not rewrite existing history or delete archived provenance unless explicitly requested.

## Session closeout

After substantial work:

1. verify actual outputs/diff;
2. update detailed project-native records where appropriate;
3. refresh root durable state if the top-level picture changed;
4. create a handoff under `.agent/handoffs/` when another conversation/device may continue;
5. record unresolved items explicitly;
6. commit/push only when requested or when the current project task explicitly includes synchronization.
