#!/usr/bin/env python3
"""
Daily portfolio summary with 7-day trend.
- Fetches latest values for Poduszka, IKE, Inwestycyjny from myFund via get_portfolio.py
- Computes daily percentage change and 7-day trend (approx. weekly)
- Persists a short history to compute trends over time
- Requires MYFUND_API_KEY to be set
"""
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

# Customize this list with your own portfolio names from myFund.pl
PORTFOLIOS = ["Alfa", "Beta", "Gamma"]

BASE_PATH = Path(__file__).parent.parent
GET_PORTFOLIO_PATH = Path(__file__).parent / "get_portfolio.py"
HISTORY_PATH = Path(__file__).parent.parent / "portfolios_history.json"

def fetch_portfolio_value(name: str):
    cmd = ["python3", str(GET_PORTFOLIO_PATH), "--portfel", name, "--format", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, cwd=str(BASE_PATH), env={**os.environ})
        data = json.loads(result.stdout)
        # get_portfolio.py zwraca JSON w formie: {"<portfel>": {"portfel": {...}}}
        # więc wartość trzeba pobrać z podklucza o nazwie portfela.
        pf_obj = data.get(name) if isinstance(data, dict) else {}
        portfel_obj = {}
        if isinstance(pf_obj, dict):
            portfel_obj = pf_obj.get("portfel") or {}
        if not portfel_obj and isinstance(data, dict):
            # awaryjnie (jeśli format odpowiedzi się zmieni)
            portfel_obj = data.get("portfel") or {}
        val = portfel_obj.get("wartosc")
        if val is None:
            return None
        # wartosc sometimes is a string; convert to float
        if isinstance(val, str):
            val_num = val.replace(",", "")
        else:
            val_num = str(val)
        return float(val_num)
    except Exception as e:
        print(f"Error fetching portfolio '{name}': {e}", file=sys.stderr)
        return None

def load_history(path: Path):
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {p: [] for p in PORTFOLIOS}
    else:
        return {p: [] for p in PORTFOLIOS}

def save_history(path: Path, hist: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)

def main():
    api_key = os.environ.get("MYFUND_API_KEY")
    if not api_key:
        print("ERROR: MYFUND_API_KEY is not set. Set it (e.g., export MYFUND_API_KEY=your_key) and rerun.", file=sys.stderr)
        sys.exit(2)

    today = date.today().isoformat()

    history = load_history(HISTORY_PATH)
    report_lines = []
    report_lines.append(f"Daily portfolio summary for {today}")
    report_lines.append("")

    # fetch current values and build per-portfolio data
    current_values = {}
    daily_changes = {}
    weekly_changes = {}

    for port in PORTFOLIOS:
        val = fetch_portfolio_value(port)
        current_values[port] = val
        if port in history and len(history[port]) >= 2 and val is not None:
            yesterday = history[port][-1] if len(history[port]) >= 2 else None
            # if history stores previous value before today, else rely on appended
        # We'll compute daily change by looking at previous history entry (before today)
        if history[port] and val is not None:
            yesterday_val = history[port][-1]
            if isinstance(yesterday_val, (int, float)) and yesterday_val != 0:
                daily_changes[port] = ((val - yesterday_val) / yesterday_val) * 100
            else:
                daily_changes[port] = None
        else:
            daily_changes[port] = None

        # Compute 7-day trend if we have 8 or more history points after appending today
        if val is not None:
            hist_list = history.get(port, [])
            # after appending today, but we haven't yet appended; we'll handle after
            weekly_changes[port] = None
        else:
            weekly_changes[port] = None

    # Update history with today's values and compute weekly trends based on 7 days ago
    for port in PORTFOLIOS:
        val = current_values[port]
        if port not in history:
            history[port] = []
        # append current value
        history[port].append(val if val is not None else 0.0)
        # keep last 8 entries to compute 7 days ago value
        if len(history[port]) > 8:
            history[port] = history[port][-8:]
        # compute 7-day trend if we have at least 8 entries
        if len(history[port]) >= 8 and history[port][-8] != 0:
            seven_days_ago = history[port][-8]
            weekly_changes[port] = ((val - seven_days_ago) / seven_days_ago) * 100 if val is not None else None
        else:
            weekly_changes[port] = None

    save_history(HISTORY_PATH, history)

    # Build human-friendly report
    for port in PORTFOLIOS:
        val = current_values[port]
        if val is None:
            report_lines.append(f"{port}: ERROR - data unavailable")
            continue
        # daily change percent
        daily_pct = daily_changes.get(port)
        daily_str = f"{daily_pct:.2f}%" if isinstance(daily_pct, float) else "-"
        # weekly trend percent (7d)
        wk_pct = weekly_changes.get(port)
        wk_str = f"{wk_pct:.2f}%" if isinstance(wk_pct, float) else "-"
        report_lines.append(f"{port}:")
        report_lines.append(f"  Wartość: {val:.2f} PLN")
        report_lines.append(f"  Zmiana dzienna: {daily_str}")
        report_lines.append(f"  Trend tygodniowy (7d): {wk_str}")
        report_lines.append("")

    # Output summary
    print("\n".join(report_lines))

if __name__ == "__main__":
    main()
