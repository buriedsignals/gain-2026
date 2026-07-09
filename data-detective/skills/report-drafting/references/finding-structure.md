# Required structure per finding (HTML)

Every `<section class="finding">` MUST contain, in order:

1. **Header row** — `<h2>` with embedded finding ID + `.pill-novel` (purple, genuinely new evidence) OR `.pill-connected` (outline, new framing of public facts), plus `.pill-high` / `.pill-med` / `.pill-low` for confidence.
2. **Deck** — one-line subhed under the H2 in `<p class="deck">` (≤60ch). The deck is a summary layer: it must be entailed by the finding body, including every caveat the body carries (see `citation-discipline.md` § summary-layer entailment).
3. **Stats grid** (optional) — `<div class="stats">` for findings with a quantitative spine.
4. **Body paragraphs** — `<p>` (auto-constrained to ≤72ch via column width). Quote primary-source text via Read of the archived page, never paraphrase from memory.
5. **`<div class="path" aria-label="How we got here">`** — REPLICATION PATH. One `.step` + `.what` pair per phase that produced this finding. Cite SQL hashes, script paths, archived URLs — all from the finding's citation manifest. This block is what makes the finding auditable in under a minute. **Mandatory.**
6. **`<div class="sources">`** — primary-source URLs with archive references. **Mandatory.**

Optional add-ins:

- `<div class="flag">` for legal qualifications — use `<span class="flag-label">` for the inline label, NOT `<strong style="display:block">` (that breaks inline legal citations onto new lines).
- `<div class="timeline">` for chronological evidence chains (4-column grid: date, event, source).
- `<div class="pull">` for a 1-2 sentence pull quote inside the finding body.

**Novelty labeling:** if the finding's core claim has already been published by a mainstream outlet, it gets `.pill-connected`, not `.pill-novel`, and the novel sub-element (typically a cross-corpus join or a specific person's institutional history) is called out in an explicit "Novelty" paragraph at the top of the body. Prize panels read the novelty framing first; mislabeling a wire-reported timeline as "novel" is a credibility hit.
