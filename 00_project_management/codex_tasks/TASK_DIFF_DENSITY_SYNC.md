# TASK_DIFF_DENSITY_SYNC

## Objective
Prepare publication-quality difference density data for the OER *OH -> *O transition.

The purpose is to reveal how Al substitution changes charge and spin reconstruction pathways.

## Systems (strict)

Use only the validated structures:

1. pristine CoOOH active Co site
2. Al-substituted CoOOH neighboring active Co site

States:
- *OH
- *O

Do not use old test structures or wrong active sites.

## Required maps

For both systems prepare:

1. charge density difference
   Δρ(r)=ρ(*O)-ρ(*OH)

2. magnetization density difference
   Δm(r)=m(*O)-m(*OH)

3. spin-up density difference

4. spin-down density difference

## Workflow rules

- Do not run new DFT calculations.
- Search existing server/local results first.
- Reuse CHGCAR, PARCHG, CHG, spin density, cube/vtk exports or previous scripts if available.
- Extract lightweight plot-ready data rather than uploading huge volumetric files.

## Required outputs

Create:

04_VASP_analysis/diff_density_publication_data/

including:

- README.md
- PROVENANCE.md
- source_manifest.tsv
- mapping/state_mapping.tsv
- mapping/slice_definition.tsv

and four folders:

- charge_density
- magnetization
- spin_up
- spin_down

Each map requires reusable TSV data containing:

x_A
y_A
value
system
transition
map_type
units
plane_label

## Slice requirements

The selected slice must include:

- active Co
- adsorbed O
- bridge O
- Al when relevant

Pristine and Al-substituted systems must use comparable orientation and plotting window.

Record:

- plane definition
- coordinate convention
- grid size
- units
- visualization range

## Provenance

Record original calculation paths, source files, extraction method, and software used.

## Validation

Before commit run:

python tools/validators/validate_diff_density_sync.py

## Final report

Return:

1. source locations
2. synchronized systems
3. available maps
4. validator result
5. commit SHA
