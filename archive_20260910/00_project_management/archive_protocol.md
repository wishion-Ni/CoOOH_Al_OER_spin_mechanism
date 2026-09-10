# CoOOH_Al_OER_spin_mechanism

# Codex Research Archive Protocol

## Purpose

This document defines the workflow for Codex to organize, archive, and
maintain the CoOOH_Al_OER_spin_mechanism project.

The goal is not to redo calculations. The goal is to preserve
computational history, collect useful datasets, separate candidate
manuscript data from historical calculations, and establish reproducible
links between experiment, theory questions, calculations, and figures.

The GitHub repository should become the central knowledge base for
manuscript preparation.

------------------------------------------------------------------------

## Scientific background

The project investigates why Al substitution in cobalt oxyhydroxide
(CoOOH) improves the OER *OH → *O conversion.

Experimental constraints:

1.  Al substitution lowers the energetic cost of the *OH → *O step.
2.  TAS indicates Co electronic/species evolution in pristine CoOOH.
3.  After Al substitution, the Co response is suppressed.
4.  The first OER step increases slightly (\~0.2 eV).
5.  For pristine CoOOH:
    -   s2+s3 is approximately 3.2 eV.
    -   s2 is the rate determining step.

Main hypothesis:

Al substitution enables a different charge/spin response pathway:

Al substitution → modified local electronic environment → suppressed
Co-centered reconstruction → alternative oxygen-related oxidation
pathway → accelerated *OH → *O conversion.

------------------------------------------------------------------------

## Archive philosophy

Do not treat all existing calculations as equally valid.

The project contains: - optimized datasets; - exploratory
calculations; - parameter tests; - failed calculations; - superseded
structures.

Every dataset must be classified.

------------------------------------------------------------------------

## Dataset classification

Every archived dataset requires a status:

### candidate_dataset

Already judged useful for manuscript-level analysis.

### supporting_dataset

Useful for interpretation or supplementary information.

### historical_dataset

Important for reproducibility but not intended for manuscript figures.

------------------------------------------------------------------------

## Data acquisition workflow

Computational files may exist in:

1.  Local computer.
2.  Remote calculation server.
3.  Previous Codex working directory.
4.  Existing GitHub repository.

Always determine file location before upload.

------------------------------------------------------------------------

## Server data handling protocol

Many important files are stored on servers.

If server access is available:

Prefer:

server → GitHub

If direct upload is impossible:

server → local computer → GitHub

For very large files:

Do not upload blindly.

Upload: - input files; - processed data; - scripts; - final
structures; - selected charge/spin data.

Compress: - selected trajectories; - selected outputs.

Do not upload: - huge wavefunction files; - temporary files; -
duplicated outputs.

Instead create a manifest containing: - filename; - size; - server
path; - calculation purpose.

------------------------------------------------------------------------

## Repository structure

    00_project_management/
    01_experimental_constraints/
    02_DFT_CP2K/
    03_cDFT/
    04_VASP_analysis/
    05_analysis_scripts/
    06_figures/
    07_literature/
    manuscript/

------------------------------------------------------------------------

## Important candidate datasets

### OER free-energy staircase

Location:

02_DFT_CP2K/OER_free_energy/

Selected curves:

### Undoped CoOOH

Black curve.

Role: Pristine reference.

Requirements: - s2+s3 ≈ 3.2 eV - s2 rate determining

### Al-neighbor Co site

Green curve.

Example: Al16 site03 Co7_adjAl

Role: Main catalytic comparison.

Purpose: Show Al modifies neighboring Co activity.

### Al site

Red curve.

Example: Al16 site02 Al47

Role: Control calculation.

Purpose: Demonstrate Al itself is not the active center.

------------------------------------------------------------------------

## cDFT dataset

Location:

03_cDFT/

Important transition:

*OH → *O

Archive: - charge redistribution; - spin evolution; - constrained-state
fingerprints.

Purpose:

Explain:

Undoped: Co-centered charge/spin reconstruction.

Al substituted: Reduced Co reconstruction and altered oxygen response.

------------------------------------------------------------------------

## Charge density difference

Location:

04_VASP_analysis/

Archive: - Δrho; - Δm; - spatial maps.

Purpose: Visualize electronic redistribution.

------------------------------------------------------------------------

## Metadata requirement

Every important dataset requires metadata.md.

Include:

-   Dataset name
-   Status
-   Source
-   Calculation method
-   Software and parameters
-   Structure information
-   Scientific purpose
-   Key observation
-   Mechanistic relevance
-   Limitations
-   Related datasets

------------------------------------------------------------------------

## Conversation archive

Create:

00_project_management/conversation_history/

Summarize: - mechanism evolution; - important decisions; - rejected
hypotheses; - unresolved questions.

Do not copy raw conversations.

------------------------------------------------------------------------

## Figure archive

For every figure:

    figure_name/
        figure.png
        source_data/
        plotting_script/
        README.md

README should describe: - scientific purpose; - datasets used; - current
status; - possible manuscript location.

------------------------------------------------------------------------

## Conflicting calculations

Never delete conflicting results.

Create:

conflicting_results.md

Explain: - calculation differences; - structural differences; -
parameter differences; - current preferred dataset.

------------------------------------------------------------------------

## Final report after archive

Provide:

1.  Repository tree.
2.  Uploaded datasets.
3.  Files remaining on server.
4.  Files requiring manual download.
5.  Candidate manuscript figures.
6.  Missing calculations needed for final mechanism.

------------------------------------------------------------------------

## Important restrictions

Do not: - rerun calculations; - modify scientific conclusions; - rename
candidate datasets as final results; - delete historical calculations.

Archive first. Interpret later.
