# 10: End-to-end validation, citations, and demo recording

**What to build:** Final polish. A worked example in `examples/worked_example.ipynb` (or `.py`) that reproduces one published TNO/CCPS case study end to end with our package. `CITATIONS.md` is fully populated. A short `DEMO.md` with a 2-minute demo script. A manual test plan in `tests/manual_checklist.md` that an evaluator can run without Python knowledge.

**Blocked by:** 09

**Status:** ready-for-agent

- [ ] `examples/worked_example.py`: picks a CCPS or TNO worked example (e.g. a propane BLEVE-adjacent scenario or a vapor cloud explosion with given E and distance), runs it through our package, asserts the output matches the published answer
- [ ] `CITATIONS.md` lists every cited reference with section/page numbers used in code
- [ ] `DEMO.md` is a 2-minute script for presenting: "Place a tank here. Pick LPG. Here's the zones. Drag wind. Notice the downwind elongation. Switch fuel. Notice hydrogen has bigger lethal radius."
- [ ] `tests/manual_checklist.md` lists 5–7 things a reviewer can check by eye (zones visible, wind rotates zones, fuel changes zones, disclaimer present, distances quoted)
- [ ] `pytest -q` is green, `ruff check` is green, the app runs