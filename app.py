import os
import random
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)

SERVICE_NAME = "cicd-test"
COHORT = os.environ.get("DEPLOYMENT_COHORT", "baseline")
IS_CANARY = (COHORT.lower() == "canary")

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{version_title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: {bg_gradient};
      color: #ffffff;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    .card {{
      background: rgba(15, 23, 42, 0.85);
      backdrop-filter: blur(12px);
      border: 2px solid {border_color};
      border-radius: 20px;
      padding: 3rem 3.5rem;
      text-align: center;
      box-shadow: 0 25px 70px rgba(0, 0, 0, 0.5);
      max-width: 520px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.6rem;
      background: {badge_bg};
      color: {badge_color};
      border: 1px solid {badge_border};
      border-radius: 999px;
      padding: 0.45rem 1.2rem;
      font-size: 0.9rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }}
    .dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: {dot_color};
      box-shadow: 0 0 10px {dot_color};
    }}
    h1 {{
      margin: 1.5rem 0 0.75rem;
      font-size: 2.2rem;
      font-weight: 800;
      letter-spacing: -0.02em;
    }}
    p.message {{
      color: #94a3b8;
      font-size: 1.1rem;
      margin: 0 0 1.75rem;
    }}
    .meta {{
      font-size: 0.85rem;
      color: #64748b;
      border-top: 1px solid #334155;
      padding-top: 1.25rem;
      line-height: 1.7;
    }}
    code {{
      background: #0f172a;
      padding: 0.2rem 0.5rem;
      border-radius: 4px;
      color: #38bdf8;
    }}
  </style>
</head>
<body>
  <div class="card">
    <span class="badge"><span class="dot"></span> {badge_text}</span>
    <h1>{version_heading}</h1>
    <p class="message">{version_desc}</p>
    <div class="meta">
      Cohort: <code>{cohort}</code> &nbsp;·&nbsp; Service: <code>{service_name}</code><br />
      Health Check: <code>/healthz</code> &nbsp;·&nbsp; Checkout: <code>/api/checkout</code><br />
      Served at: {timestamp}
    </div>
  </div>
</body>
</html>
"""


def _render_index():
    if IS_CANARY:
        return INDEX_HTML.format(
            version_title="VERSION 2 — NEW RELEASE (CANARY)",
            version_heading="VERSION 2 — NEW RELEASE",
            version_desc="Canary evaluation cohort with simulated elevated error rate on checkout.",
            bg_gradient="linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%)",
            border_color="#6366f1",
            badge_bg="rgba(99, 102, 241, 0.2)",
            badge_color="#a5b4fc",
            badge_border="rgba(99, 102, 241, 0.4)",
            dot_color="#818cf8",
            badge_text="CANARY COHORT",
            cohort=COHORT,
            service_name=SERVICE_NAME,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )
    else:
        return INDEX_HTML.format(
            version_title="VERSION 1 — STABLE (BASELINE)",
            version_heading="VERSION 1 — STABLE",
            version_desc="Production baseline serving 99.9% healthy transactions.",
            bg_gradient="linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%)",
            border_color="#10b981",
            badge_bg="rgba(16, 185, 129, 0.2)",
            badge_color="#6ee7b7",
            badge_border="rgba(16, 185, 129, 0.4)",
            dot_color="#34d399",
            badge_text="BASELINE COHORT",
            cohort=COHORT,
            service_name=SERVICE_NAME,
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )


def _handle_checkout():
    # If canary: 25% hardcoded failure rate to trip Wald SPRT (p1=0.020, alpha=0.01)
    # If baseline: 1% failure rate (well below p0=0.005 / ambient acceptable noise)
    failure_probability = 0.25 if IS_CANARY else 0.01
    if random.random() < failure_probability:
        return jsonify({
            "status": "error",
            "error": "Payment processing failed",
            "cohort": COHORT,
            "is_canary": IS_CANARY
        }), 500
    return jsonify({
        "status": "success",
        "message": "Checkout completed",
        "cohort": COHORT,
        "is_canary": IS_CANARY
    }), 200


@app.route("/", methods=["GET"])
def index():
    return _render_index()


@app.route("/api/hello", methods=["GET"])
def hello():
    return jsonify({"message": "hello from smartcd-test", "cohort": COHORT})


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "ok", "cohort": COHORT}), 200


@app.route("/api/checkout", methods=["POST", "GET"])
def checkout():
    return _handle_checkout()


@app.route("/<path:path>", methods=["GET", "POST"])
def catch_all(path):
    tail = path.rstrip("/").rsplit("/", 1)[-1]
    if tail == "healthz":
        return jsonify({"status": "ok", "cohort": COHORT}), 200
    if tail == "hello":
        return jsonify({"message": "hello from smartcd-test", "cohort": COHORT})
    if tail == "checkout":
        return _handle_checkout()
    return _render_index()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

