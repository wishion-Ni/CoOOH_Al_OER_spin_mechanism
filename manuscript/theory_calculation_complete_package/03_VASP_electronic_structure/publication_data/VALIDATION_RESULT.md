# Synchronization validation

Validation command:

`python tools/validate_cohp_pdos_sync.py`

Result on 2026-09-13:

`PASS: COHP/ICOHP/PDOS synchronization validated; 0 hard errors`

Validated counts: 4 states, 12 geometry-checked mapping rows, 12 ICOHP
rows, 9,624 spin-resolved COHP rows, and 14,660 PDOS rows.

The compact tables were regenerated from the authorized server extraction
directory `/home/ftfan/ncw/sync_server_extract_20260913_run4` after correcting
the spin-polarized COHPCAR interaction-column parser. No electronic-structure
calculation was started for this synchronization. COHP and PDOS curves are
stored as four state-specific shards; the validator merges them for checks.

