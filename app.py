import os
from datetime import datetime, timezone

from flask import Flask, jsonify

app = Flask(__name__)

SERVICE_NAME = "smartcd-test"

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>smartcd-test — live</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: linear-gradient(135deg, #0f172a, #1e293b);
      color: #e2e8f0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    .card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 16px;
      padding: 2.5rem 3rem;
      text-align: center;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
      max-width: 420px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(34, 197, 94, 0.15);
      color: #4ade80;
      border: 1px solid rgba(34, 197, 94, 0.3);
      border-radius: 999px;
      padding: 0.35rem 0.9rem;
      font-size: 0.8rem;
      font-weight: 600;
      letter-spacing: 0.02em;
    }}
    .dot {{
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #4ade80;
      box-shadow: 0 0 8px #4ade80;
    }}
    h1 {{
      margin: 1.25rem 0 0.5rem;
      font-size: 1.6rem;
    }}
    p.message {{
      color: #94a3b8;
      margin: 0 0 1.5rem;
    }}
    .meta {{
      font-size: 0.75rem;
      color: #64748b;
      border-top: 1px solid #334155;
      padding-top: 1rem;
      line-height: 1.6;
    }}
    code {{
      background: #0f172a;
      padding: 0.15rem 0.4rem;
      border-radius: 4px;
      color: #7dd3fc;
    }}
  </style>
</head>
<body>
  <div class="card">
    <span class="badge"><span class="dot"></span> LIVE</span>
    <h1>{service_name}</h1>
    <p class="message">"{message}"</p>
    <div class="meta">
      Served at {timestamp}<br />
      Health check: <code>/healthz</code> &nbsp;·&nbsp; JSON: <code>/api/hello</code>
    </div>
  </div>
</body>
</html>
"""


def _render_index():
    return INDEX_HTML.format(
        service_name=SERVICE_NAME,
        message="hello from smartcd-test",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    )


@app.get("/")
def index():
    return _render_index()


@app.get("/api/hello")
def hello():
    return jsonify({"message": "hello from smartcd-test"})


@app.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


# The platform's ALB routes a project behind a path prefix (e.g.
# /api/v1/cicd-test) and forwards the FULL, unstripped path to the
# container — it never rewrites it back to "/". Without this, every
# real request through the live URL 404s even though the exact same
# routes work perfectly under docker run/local testing, where nothing
# prepends a prefix. This catches any path Flask's exact routes above
# didn't already match, and still honors the last path segment so
# "<prefix>/healthz" and "<prefix>/api/hello" keep their real meaning
# no matter what prefix a given onboarding assigns.
@app.get("/<path:path>")
def catch_all(path):
    tail = path.rstrip("/").rsplit("/", 1)[-1]
    if tail == "healthz":
        return jsonify({"status": "ok"}), 200
    if tail == "hello":
        return jsonify({"message": "hello from smartcd-test"})
    return _render_index()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
