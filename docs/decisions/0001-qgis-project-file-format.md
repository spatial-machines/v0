# QGIS Project File Format Resolution — SIGNED OFF

Status: **RESOLVED — `.qgs` (plain XML) selected as the firm canonical QGIS project file format. MW-13 wiki patches unblocked.**
Date: 2026-04-09 (drafted), 2026-04-09 (signed off)
Resolution: standardize on `.qgs` because that is what the live pipeline already produces. The contradiction is resolved by updating the wiki page to match production behavior, not by changing production behavior to match the wiki page.

This doc is the MW-13 counterpart to `docs/CARTOGRAPHY_REQUIREMENT_RESOLUTION.md`. Same pattern: a contradiction needing human sign-off, captured in a small artifact, then unblocking the migration.

---

## 1. The Contradiction

`docs/WAVE2_MW13_QGIS_CONSOLIDATION_DRAFT.md` §4.1 documented a four-source disagreement on the QGIS project file format used by the firm:

| Source | Format | Status |
|---|---|---|
| `docs/wiki/workflows/QGIS_HANDOFF_PACKAGING.md` (existing wiki canon) | `.qgz` (compressed) | **Outlier** |
| `handbooks/workflows/qgis-bridge-and-review.md` (operational handbook) | `.qgs` (plain XML) | majority |
| `docs/QGIS_PROJECT_CONTRACT.md` (technical contract for the auto-generation pipeline) | `.qgs` | majority |
| `handbooks/cartography/qgis-review-conventions.md` (cartography conventions) | not specified | abstain |
| **Live runtime** — `build_qgis_project.py` (the script the firm actually runs in production) | `.qgs` | majority |

Three of four documented sources, plus the live runtime, say `.qgs`. The wiki page is the only outlier.

## 2. Why the Wiki Page Said `.qgz`

The wiki page was authored as a general-purpose workflow rather than as a description of the firm's current pipeline. `.qgz` is the modern QGIS default and is generally recommended for delivery (it bundles the project file with embedded styles into a single zipped artifact). The wiki page took the modern-default approach. The firm's actual practice diverged.

## 3. Why `.qgs` Wins on the Resolution

- **The live pipeline produces `.qgs`.** Changing the runtime to produce `.qgz` is a non-trivial change to `build_qgis_project.py` and any downstream consumers. Updating the wiki page to say `.qgs` is a one-sided text edit with no downstream cost.
- **The QGIS Project Contract specifies `.qgs`.** That contract is the technical authority for the auto-generation pipeline; the wiki page should not contradict it.
- **The handbook (the operational source) says `.qgs`.** Agents currently following the handbook produce `.qgs` files; the wiki should not push them to a different format.
- **`.qgs` is plain XML and diffable.** This is a real operational advantage for review packages: a reviewer can compare two project files in a text diff. `.qgz` is a zipped archive that requires unpacking before diffing.
- **Both formats are equally readable by QGIS 3.x.** No QGIS version compatibility concern either way.
- **The drift risk if the contradiction is left unresolved is HIGH** (per draft §6, drift risks): agents following the wiki would expect `.qgz` while the pipeline produces `.qgs`, causing validation failures or confusing reviewer instructions.

The lower-cost, lower-risk resolution is to update the wiki page text. The runtime, the contract, and the handbook all stay as-is.

## 4. What This Resolution Authorizes

After this doc is signed off, MW-13 wiki patches may execute. Specifically:

1. The body of `docs/wiki/workflows/QGIS_HANDOFF_PACKAGING.md` may be updated to say `.qgs` everywhere it currently says `.qgz`. This includes:
   - Phase 2 step 1 ("Create a new QGIS project file") — currently says `.qgz`
   - Outputs section — currently says `.qgz`
   - Common Failure Modes — currently flags "delivering a .qgs file (XML, large) instead of .qgz" as a failure; this becomes inverted (delivering a `.qgz` when the pipeline expects `.qgs` is the failure mode)
2. The MW-13 draft §2.1 "Reviewer Guidance" section instruction to "open `project.qgz`" is updated to say "open `project.qgs`".
3. The new "Layer and Styling Conventions" section may reference `.qgs` consistently.

## 5. What This Resolution Does Not Authorize

- No edits to the runtime pipeline (`build_qgis_project.py`).
- No edits to `docs/QGIS_PROJECT_CONTRACT.md`.
- No edits to `handbooks/workflows/qgis-bridge-and-review.md` beyond what MW-13 §5 prescribes (the handbook flip eventually happens, but per the discipline that gates on production validation, this doc does not authorize an early flip).
- No edits to `handbooks/cartography/qgis-review-conventions.md` beyond MW-13 §5.

## 6. What If `.qgz` Becomes the Right Choice Later?

If the firm later decides to migrate the pipeline to produce `.qgz` (for client deliveries that benefit from the single-file format, for example), that is a separate, larger migration. It would require:

1. Updating `build_qgis_project.py` to produce `.qgz`
2. Updating `docs/QGIS_PROJECT_CONTRACT.md` to specify `.qgz`
3. Updating the wiki page (a second time) to say `.qgz`
4. Updating any downstream consumers that read the project file
5. Production validation that the `.qgz` output works end-to-end with the firm's review tooling

That migration is out of scope for this resolution and is not currently planned. The resolution here is the simpler reverse: update the wiki page to match what the pipeline already does.

## 7. Sign-off Block

**Reviewer**: human (project owner)
**Date**: 2026-04-09
**Decision**: standardize on `.qgs` (matches pipeline + handbook + project contract)

**Notes**: This is the lower-cost, lower-risk resolution. The wiki page was the outlier; aligning it with the runtime is a one-sided edit with no downstream cost. If the firm later wants to move the pipeline to `.qgz`, that is a separate migration and will need its own planning artifact.

## 8. After Sign-off

Once this document is signed off:

1. MW-13 Patch 1 (the wiki page extensions in `QGIS_HANDOFF_PACKAGING.md`) may execute.
2. The wiki page body is updated to use `.qgs` consistently.
3. The handbook ledger rows for `workflows/qgis-bridge-and-review.md` and `cartography/qgis-review-conventions.md` are annotated `(live — pending production validation)`.
4. Per the session discipline, neither handbook is flipped to `migrated` until production validation has run.
5. The Common Failure Modes entry that currently says "delivering a .qgs file (XML, large) instead of .qgz" is rewritten to reflect the `.qgs`-canonical reality.
