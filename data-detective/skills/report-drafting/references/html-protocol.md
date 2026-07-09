# HTML editing protocol (hard rule)

NEVER run greedy regex substitution on the HTML file. Use `Read` + `Edit` with anchored old_strings only. A greedy `re.sub` destroyed the entire report.html mid-pass in a prior investigation and forced a full rebuild.

Specifically:

- For per-finding additions: anchor `old_string` on the closing element of the prior block + the opening of the target block.
- For methodology restructuring: extract the existing section, rewrite as a single block, replace with one `Edit` call.
- If you must regex, do it in a one-shot Python script that prints the diff first, never `re.sub(..., re.DOTALL)` on the whole file.

## Validation + smoke test (before declaring P5 complete)

1. Tag-balance check:
   ```bash
   python3 - <<'PY'
   from html.parser import HTMLParser
   import sys
   VOID = {"area","base","br","col","embed","hr","img","input","link","meta","source","track","wbr"}
   class P(HTMLParser):
       def __init__(self): super().__init__(); self.stack=[]
       def handle_starttag(self, t, a):
           if t not in VOID: self.stack.append(t)
       def handle_endtag(self, t):
           if not self.stack or self.stack.pop() != t: print("MISMATCH near", t, self.getpos())
   p=P(); p.feed(open("case/report.html").read())
   print("unclosed:", p.stack if p.stack else "none")
   PY
   ```
2. Open `report.html` in a browser; visual smoke test — TL;DR anchors jump, pills render, `.path` blocks aligned, no clipped labels.
