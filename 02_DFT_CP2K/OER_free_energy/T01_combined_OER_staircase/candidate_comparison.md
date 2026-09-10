# Candidate Comparison

The archive contains more than one processed OER candidate. They are not averaged or mixed because their source branches and/or correction histories are not identical.

| Candidate | Step 1 | Step 2 | Step 3 | Step 4 | Decision |
|---|---:|---:|---:|---:|---|
| undoped Co32 | 1.199993 | 1.793143 | 1.534211 | 0.392652 | selected pristine reference |
| Al16 Co7 adjAl | 2.978921 | 0.968096 | 1.226737 | -0.253754 | selected active Co adjacent to Al |
| Al16 Al47 | 2.172485 | 0.371060 | 0.822645 | 1.553810 | selected Al control |
| Al16 Co13 adjAl | 0.380548 | 3.588861 | 3.422753 | -2.472163 | excluded from main comparison; different site branch |
| Al16 Co19 far | -5.715297* | 3.262888* | 1.516971* | 5.855439* | excluded; far-Co control and different processed branch |

`*` The Al16 Co19 row is shown only as a branch inventory; its exact four-step values are retained in `cooh_oer_thermo_steps_20260523.tsv` and are not used to construct the T01 source table.

The selected table is the compact processed record `cooh_al16_undoped_oer_steps.csv`. The archived metadata explicitly labels the broader CP2K OER records as candidate/supporting data and warns that historical staircase values come from multiple branches. That limitation is retained here rather than hidden.
