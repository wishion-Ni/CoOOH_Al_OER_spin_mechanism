# Metadata: CP2K OER Free-Energy Records

- **Status:** candidate/supporting, depending on source file.
- **Source:** selected files from the local `outputs/` tree and validated CP2K source records.
- **Method:** CP2K geometry/thermochemistry records and conventional four-step AEM/CHE bookkeeping.
- **Purpose:** establish the energetic trend and identify the *OH -> *O step for electronic-mechanism analysis.
- **Key observation:** the pristine reference is expected to retain `s2+s3` near 3.2 eV with `s2` rate determining; Al selectively improves the key conversion while the first step becomes slightly less favorable.
- **Limitations:** archived staircase values come from multiple historical branches and are not silently normalized into one final dataset.
- **Related data:** `03_cDFT`, `04_VASP_analysis`, and `manuscript/evidence_to_claims.md`.
