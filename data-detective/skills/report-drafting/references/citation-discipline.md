# Citation discipline (hard rule — learned the hard way, twice)

**The synthesis layer must NEVER originate a primary-source citation.** Every UUID, every external URL, every filing reference, every direct quote MUST be copied verbatim from a ground-truth file written by an earlier phase. If a citation is not already in the trail, do not invent it — go fetch it.

The failure mode this prevents: a synthesis pass that "looks right" but contains URLs and UUIDs the LLM generated from semantic memory, that 404 or resolve to the wrong filing under adversarial review. This is the most common way investigative-journalism submissions get killed. Both post-publication verification passes on the GAIN-2026 case (2026-05-25 and 2026-07-09) found exactly this class of drift — and the 07-09 pass found it had migrated **up a layer**: bodies were correct, but README bullets, TL;DR rows, and evidence-table attributions had drifted. Summary layers are citations too.

## Build the per-finding citation manifest FIRST

Before drafting any finding, extract its allowed citation set:

- From data-detective: `findings.json` `supporting_cards` + `external_sources` + `supporting_query_hashes`.
- From spotlight (if `promoted_from` is set): `case-trace/spotlight/results/<OS-NNN>/data/findings.json` `external_sources` + `research/*.md` filenames + `investigation-log.json` `urls_accessed`.
- Write the manifest to `/tmp/c-NNN-citations.txt` — this is the ALLOWED set for this finding. **Any URL or UUID in the draft must appear in this file. No exceptions.**

## Sources of truth (in priority order)

1. `case-trace/spotlight/results/*/research/*.md` — the literal scraped page text. URL of the original is in the filename, the file's frontmatter, or `investigation-log.json` under `urls_accessed`.
2. `case-trace/spotlight/results/*/data/findings.json` — the investigator's curated source list per finding (`external_sources` arrays).
3. `case-trace/data-detective/cards/senate_filing_<UUID>.md` — evidence cards generated deterministically from the DuckDB index. The UUID in the filename IS the canonical UUID.
4. `case-trace/data-detective/anomalies/*.provenance.json` — SQL hashes and detector SQL.
5. `case-trace/data-detective/external/factcheck/*` — adversarial fact-checker archives.

## Required before any external URL or UUID lands in the draft

```bash
# Pattern A — UUID is a Senate LDA filing
grep -rln "<UUID>" case-trace/spotlight/results/ case-trace/data-detective/cards/
# Must return at least one ground-truth file. If empty: STOP. Do not paste this UUID.

# Pattern B — external URL (news article, gov page, etc.)
grep -rln "<URL>" case-trace/spotlight/results/
# Must return at least one ground-truth file. If empty AND the URL is not already in
# case-trace/data-detective/external/, STOP.
# To add a URL: firecrawl-scrape it first, write under case-trace/data-detective/external/, then it is grep-able.
```

If a fact has no ground-truth file, either **drop the claim** (synthesis documents what was verified upstream; it does not introduce new facts) or **fetch it** (one-shot firecrawl scrape → `case-trace/data-detective/external/<slug>-<yyyymmdd>.md` → cite). Never paraphrase or "remember" a URL.

## Attribute at the filing level, not the aggregate level

Four traps that survived one verification pass each on GAIN-2026 — treat these as citation rules, not style advice:

- **Aggregator rollups are not filing-level facts.** OpenSecrets attributes portfolio-company clients to their parent (Arconic → "Apollo Global Management"). Before asserting "X lobbies for Y," confirm Y appears as `client_name` on an actual LDA filing naming X. If only the rollup supports it, say "portfolio company Z (attributed to Y by OpenSecrets)."
- **Posted date ≠ effective date.** LDA registrations carry both; timing claims ("retained N days after the indictment") MUST read the filing's `effective_date` field via the LDA API, not the posting date on the print page. On GAIN-2026 this error ran in *both* directions across two passes.
- **Litigation is a status, not an event.** "X is suing Y" decays. Before publishing, pull the docket (CourtListener/RECAP) and state the current posture: pending / decided / on appeal. Filing-day press coverage is not a status source.
- **Registry identifiers have lifecycles.** FEC committees terminate; firms re-register under sibling names (Anchor & Arrow *Strategies* vs *LLC* are distinct Senate registrant IDs). Re-verify the identifier resolves to a live, correct entity via the primary API at draft time — the wrong committee's page can exist and still be wrong.

## What NOT to do

- ❌ Guess a `nytimes.com/<y>/<m>/<d>/<slug>.html` URL — NYT URLs aren't predictable from the headline. **Look it up.**
- ❌ Pick a plausible-looking UUID for an LDA filing. UUIDs aren't predictable. **Grep the scrape.**
- ❌ Invent timing ("retained the day after"). The LD-1 has an effective-date field; if you haven't read it, don't assert it.
- ❌ Re-derive a court case name / docket caption / counsel-of-record from memory. Pull it from the archived docket text.

## Final pre-commit closure script

Before declaring P5 complete — and note the sweep now includes the summary layers (README, TL;DR), not just the three deliverables:

```bash
# Extract every UUID and external URL from the drafted files AND summary layers
grep -ohE '[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}|https?://[^[:space:])"]+' \
  case/findings-report.md case/report.html case/evidence-map.json README.md \
  | sort -u > /tmp/p5-citations.txt

# For each, confirm it appears in ground-truth files
while read -r token; do
  if ! grep -rlq -- "$token" case-trace/spotlight/results/ case-trace/data-detective/cards/ \
       case-trace/data-detective/external/ case-trace/data-detective/anomalies/; then
    echo "ORPHAN CITATION: $token"
  fi
done < /tmp/p5-citations.txt
```

An orphan citation is a P5 bug. Fix it before declaring complete — fetch the source or remove the claim.

**Summary-layer entailment check** (the 07-09 lesson): after any correction to a finding body, grep every summary surface (README bullets, TL;DR rows, `.deck` lines, headline table) for the finding's key nouns and numbers, and confirm no summary sentence asserts something its body now disclaims. Summary layers are derived text — regenerate them from the corrected body, never patch them independently.

## Audit breadcrumbs

When you correct a previously-published citation, leave a trail — this is what makes the case-trace defensible: not "we never erred" but "we caught and corrected, with the trail in the artifact":

```json
"description": "Akin Gump LDA filing for Ant Group: UUID a4411100-... (Q1 2025 LD-2). Previous version cited UUID 3a6e17c0-... in error — that resolves to a Posco America filing. Corrected against Spotlight OS-002 archive at case-trace/spotlight/results/OS-002.../research/lda-akingump-antgroup-filing.md."
```

Every correction pass also appends a dated row to the "Corrections log" section at the end of `findings-report.md`: finding, was, now, verified-against.
