# Pre-Tier Cleanup Protocol

Run this checklist before starting any new tier of development. Takes ~30 minutes. Prevents documentation drift, broken references, and stale agent knowledge.

---

## Checklist

### 1. Documentation
- [ ] Update `README.md` — does it reflect current capabilities accurately?
- [ ] Update `ROADMAP.md` — mark completed items ✅, update in-progress
- [ ] Update `memory/PROJECT_MEMORY.md` — add lessons from last tier, update capability list
- [ ] Update `logs/lessons-learned.jsonl` — add any new lessons discovered

### 2. Agent Knowledge
- [ ] Check each agent's `TOOLS.md` — do they know about all new scripts?
- [ ] Check each agent's `SOUL.md` — are protocols current?
- [ ] Verify all agents' memory block points to current `PROJECT_MEMORY.md`

### 3. Scripts
- [ ] Run smoke test: `python scripts/smoke_test.py`
- [ ] Check for any broken imports in new scripts: `python -c "import geopandas, rasterio, rasterstats, folium, esda, spreg"`
- [ ] Archive any deprecated/replaced scripts to `scripts/deprecated/`
- [ ] Verify `requirements.txt` matches what's actually used

### 4. Config
- [ ] `config/palettes.json` — any new color needs?
- [ ] `templates/project_brief.json` — any new fields needed?
- [ ] `tool-registry/` — does it need re-ingestion if source updated?

### 5. Delivery
- [ ] QGIS packages open styled with basemap
- [ ] All output maps pass `validate_cartography.py`
- [ ] Style sidecars exist for all maps

### 6. Registry
- [ ] `analyses/registry.json` — all active projects registered?
- [ ] Any completed projects to archive?

---

## When to Run

- Before starting Tier 1 (now done — items 1-6 ✅)
- Before starting Tier 2 (items 7-13)
- Before starting Tier 3 (items 14-20)
- Before any benchmark re-run
- After any Docker rebuild

---

## Notes from Previous Cleanup (2026-04-03)

- README was describing v1 single-agent system — completely rewritten
- ROADMAP was 500 lines of mixed history — condensed to clean versioned structure
- All 10 agent SOULs updated with memory block pointing to PROJECT_MEMORY.md
- PROJECT_MEMORY.md rewritten to reflect v2b state
- 17 lessons written to lessons-learned.jsonl
- Census API key was in .env but not passed to Docker — fixed via env_file directive
