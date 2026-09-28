#!/usr/bin/env python
"""Local web page for the demo: type one of the prepared questions (or click it) and
see the verdict, the evidence with source documents, and the Dutch answer.

    venv/Scripts/python experiments/kg/kg_web.py            # serves http://127.0.0.1:8765
    venv/Scripts/python experiments/kg/kg_web.py --port 9000

Matching is lenient on case, punctuation and accents, and exact otherwise: entity
linking is not implemented yet (next step 1 in the README), so a question outside the
prepared set is reported as "niet gekoppeld". The question set lives in demo.py.
Standard library only.
"""
import html
import re
import sys
import unicodedata
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

sys.path.insert(0, str(Path(__file__).parent))
from build import build                 # noqa: E402
from query import KG, verbalise         # noqa: E402
from demo import QUESTIONS, DUTCH       # noqa: E402


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9 ]+", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


PREPARED = {norm(q): (q, t, a, why) for q, t, a, why in QUESTIONS}
KG_: KG = None   # set in main()


def lookup(question: str) -> dict:
    hit = PREPARED.get(norm(question))
    if hit is None:
        return {"linked": False, "question": question}
    q, template, args, why = hit
    v = KG_.run(template, args)
    call = f"{template}({', '.join(f'{k}={a}' for k, a in args.items())})"
    answer = DUTCH[v.verdict]
    if template == "open_on" and v.verdict == "entailed" and v.values:
        answer += " (" + ", ".join(str(x).split("#")[-1] for x in v.values) + ")"
    return {"linked": True, "question": q, "call": call, "verdict": v.verdict,
            "verdict_line": str(v), "inferred": v.inferred,
            "evidence": verbalise(v).splitlines(), "answer": answer, "why": why}


COLOUR = {"entailed": "#1b7f3b", "contradicted": "#b3261e", "unknown": "#8a6d00"}

PAGE = """<!doctype html>
<html lang="nl"><head><meta charset="utf-8">
<title>De Rode Winkel: kennisgraaf</title>
<style>
  body {{ font: 17px/1.45 system-ui, sans-serif; margin: 0; padding: 24px 16px; color: #222; background: #fafafa; }}
  main {{ max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 22px; margin: 0 0 16px; }}
  form {{ display: flex; gap: 8px; margin-bottom: 12px; }}
  input[type=text] {{ flex: 1; font-size: 18px; padding: 10px 12px; border: 1px solid #bbb; border-radius: 6px; }}
  button {{ font-size: 17px; padding: 10px 18px; border: 0; border-radius: 6px; background: #c8102e; color: #fff; cursor: pointer; }}
  .prepared a {{ display: inline-block; margin: 0 8px 8px 0; padding: 6px 10px; background: #eee; border-radius: 6px; color: #222; text-decoration: none; font-size: 15px; }}
  .prepared a:hover {{ background: #ddd; }}
  .result {{ margin-top: 20px; padding: 18px 20px; background: #fff; border: 1px solid #ddd; border-radius: 8px; }}
  .verdict {{ font-size: 20px; font-weight: 600; }}
  .answer {{ font-size: 26px; margin: 10px 0 14px; }}
  dt {{ color: #666; font-size: 14px; margin-top: 12px; }}
  dd {{ margin: 2px 0 0; }}
  pre {{ margin: 0; font: 14px/1.5 ui-monospace, Consolas, monospace; white-space: pre-wrap; }}
  .inferred {{ color: #555; font-size: 14px; }}
</style></head><body><main>
<h1>De Rode Winkel: vraag het aan de kennisgraaf</h1>
<form method="get" action="/">
  <input type="text" name="q" value="{qval}" placeholder="Typ een voorbereide vraag..." autofocus>
  <button type="submit">Vraag</button>
</form>
<div class="prepared">{links}</div>
{result}
</main></body></html>
"""


def render(r: dict | None) -> str:
    links = "".join(f'<a href="/?q={quote(q)}">{html.escape(q)}</a>' for q, *_ in QUESTIONS)
    if r is None:
        result = ""
    elif not r["linked"]:
        result = ('<div class="result"><div class="verdict" style="color:#555">niet gekoppeld</div>'
                  '<div class="answer">Daar hebben we geen informatie over</div>'
                  '<dl><dt>toelichting</dt><dd>Geen van de voorbereide vragen komt overeen. Zonder entity linking '
                  '(volgende stap 1) wordt een vraag buiten de set niet aan een template gekoppeld, en is het oordeel '
                  '"unknown".</dd></dl></div>')
    else:
        ev = html.escape("\n".join(r["evidence"])) or "(geen ondersteunende triples: niets in de graaf spreekt zich uit)"
        inf = ' <span class="inferred">(deels afgeleid door de reasoner)</span>' if r["inferred"] else ""
        result = (f'<div class="result"><div class="verdict" style="color:{COLOUR[r["verdict"]]}">{r["verdict"]}{inf}</div>'
                  f'<div class="answer">{html.escape(r["answer"])}</div><dl>'
                  f'<dt>template</dt><dd><pre>{html.escape(r["call"])}</pre></dd>'
                  f'<dt>oordeel met toelichting</dt><dd><pre>{html.escape(r["verdict_line"])}</pre></dd>'
                  f'<dt>bewijs (triple en brondocument)</dt><dd><pre>{ev}</pre></dd>'
                  f'<dt>waarom</dt><dd>{html.escape(r["why"])}</dd></dl></div>')
    return PAGE.format(qval=html.escape(r["question"]) if r else "", links=links, result=result)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        u = urlparse(self.path)
        if u.path != "/":
            self.send_response(404); self.end_headers(); return
        q = parse_qs(u.query).get("q", [""])[0].strip()
        body = render(lookup(q) if q else None).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):   # one line per request, no timestamps
        print(fmt % args)


def main(argv):
    global KG_
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else 8765
    ds, n_problems = build(write=False, quiet=True)
    if n_problems:
        print(f"build reported {n_problems} problems; fix them before serving", file=sys.stderr)
        return 1
    KG_ = KG(ds)
    print(f"graph built; serving on http://127.0.0.1:{port}  (Ctrl+C stops)")
    try:
        HTTPServer(("127.0.0.1", port), Handler).serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
