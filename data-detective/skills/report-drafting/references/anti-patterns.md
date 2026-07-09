# Anti-patterns (learned the hard way — each entry cost a correction pass)

- **Wall-of-text findings.** Every finding gets a `.path` block. If you write "we ran D11 then drilled then archived three URLs" in prose, lift it into the path block.
- **Methodology-at-the-bottom dumping ground.** Phases in phase order; fact-check and handoff tables INSIDE their phase blocks. See `methodology-pattern.md`.
- **Sources at the end of the document.** Sources go inline per-finding via the `.sources` strip.
- **Regex on the live file.** `Read` + `Edit` with anchored old_strings only. See `html-protocol.md`.
- **Citation hallucination.** The synthesis layer never originates a UUID, URL, docket caption, or quote. See `citation-discipline.md` — run the closure script.
- **Novelty inflation.** Wire-reported timelines get `.pill-connected`, not `.pill-novel`. See `finding-structure.md`.
- **Summary-layer drift** *(found 2026-07-09)*. Corrections applied to finding bodies but not to README bullets, TL;DR rows, decks, or the methodology's counts. Every error the third GAIN-2026 verification pass found lived in a summary layer above a correct body. Summary layers are derived text: regenerate from the corrected body, then run the entailment grep in `citation-discipline.md`.
- **Aggregator-rollup attribution** *(found 2026-07-09)*. "Lobbies for Apollo" sourced from OpenSecrets' parent-company rollup when the LDA client was portfolio company Arconic. Assert representation only at the filing level.
- **Posted-date-as-effective-date** *(prose-derived timing caught 2026-05-25; that correction read the wrong date field and was itself caught 2026-07-09)*. The LD-1 posting date and the client effective date differ by six weeks on the same filing. Timing claims read the `effective_date` field from the LDA API, nothing else.
- **Litigation-as-event** *(found 2026-07-09)*. "X is suing Y" published 14 months after X had lost at district court. Litigation is a status — pull the docket, state the posture (pending / decided / on appeal) with dates.
- **Dead-registry identifiers** *(found 2026-07-09)*. A $5M receipt attributed to an FEC committee that had filed its termination report a year earlier; the committee's page still existed, so a page-existence check "verified" it. Verify the identifier resolves to the *transaction*, not just to a page — and check liveness (`filing_frequency: "T"` = terminated).
- **Sibling-entity conflation** *(found 2026-07-09)*. "Anchor & Arrow Strategies" (Austin, ID 401108172) and "Anchor & Arrow LLC" (DC, ID 401110145) are distinct registrants; a covered-position claim cited a filing belonging to the other entity. When a firm has successor/sibling registrations, pin every UUID to its specific registrant ID.
