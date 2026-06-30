from __future__ import annotations

import argparse
import http.server
import socketserver
import sys
import webbrowser
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from utils.ml_training.ml_training_utils import resolve_run_dir


def _dashboard_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Live Training Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 16px; background: #0b1020; color: #e7ecff; }
    .card { background: #17203a; border: 1px solid #2e3b69; border-radius: 8px; padding: 12px; margin-bottom: 12px; }
    .label { color: #9fb0e6; font-size: 0.9rem; }
    .value { font-size: 1.1rem; font-weight: 700; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
    pre { white-space: pre-wrap; word-break: break-word; margin: 0; }
  </style>
</head>
<body>
  <h1>Live Training Dashboard</h1>
  <div class="grid">
    <div class="card"><div class="label">Event</div><div id="event" class="value">-</div></div>
    <div class="card"><div class="label">Episode</div><div id="episode" class="value">-</div></div>
    <div class="card"><div class="label">Episode Return</div><div id="ret" class="value">-</div></div>
    <div class="card"><div class="label">Episodes per second</div><div id="eps" class="value">-</div></div>
    <div class="card"><div class="label">Rolling mean return</div><div id="rolling" class="value">-</div></div>
    <div class="card"><div class="label">Latest step</div><div id="step" class="value">-</div></div>
  </div>
  <div class="card">
    <div class="label">Latest payload</div>
    <pre id="payload">{}</pre>
  </div>
  <script>
    async function readJson(path) {
      const response = await fetch(path + "?t=" + Date.now(), { cache: "no-store" });
      if (!response.ok) { return null; }
      return await response.json();
    }
    function setText(id, value) {
      document.getElementById(id).textContent = value ?? "-";
    }
    function f(x, d = 3) {
      if (x === null || x === undefined || Number.isNaN(Number(x))) return "-";
      return Number(x).toFixed(d);
    }
    async function refresh() {
      const latest = await readJson("./telemetry/latest.json");
      if (latest) {
        setText("event", latest.event);
        setText("episode", latest.episode_idx);
        setText("ret", f(latest.episode_return, 6));
        setText("eps", f(latest.episodes_per_second, 3));
        setText("rolling", f(latest.rolling_return_mean, 6));
        document.getElementById("payload").textContent = JSON.stringify(latest, null, 2);
      }
      const step = await readJson("./telemetry/current_step.json");
      if (step) {
        setText("step", "ep " + step.episode_idx + " | step " + step.step_idx + " | r " + f(step.reward, 6));
      }
    }
    refresh();
    setInterval(refresh, 1000);
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve live training dashboard for a run directory.")
    parser.add_argument("--run-id", type=str, required=True)
    parser.add_argument("--host", type=str, default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open-browser", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = resolve_run_dir(args.run_id)
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")
    dashboard_path = run_dir / "live_dashboard.html"
    dashboard_path.write_text(_dashboard_html(), encoding="utf-8")
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(run_dir), **kw)
    with socketserver.TCPServer((args.host, args.port), handler) as httpd:
        url = f"http://{args.host}:{args.port}/live_dashboard.html"
        print(f"Serving run dashboard at: {url}")
        if args.open_browser:
            webbrowser.open(url)
        httpd.serve_forever()


if __name__ == "__main__":
    main()
