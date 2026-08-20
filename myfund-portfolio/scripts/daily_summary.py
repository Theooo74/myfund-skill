#!/usr/bin/env python3
"""
Daily portfolio summary with 7-day trend.
- Fetches latest values for Poduszka, IKE, Inwestycyjny from myFund via get_portfolio.py
- Computes daily percentage change and exact 7-calendar-day trend
- Persists a short history to compute trends over time
- Requires MYFUND_API_KEY to be set
"""
import json
import math
import os
import subprocess
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

# Customize this list with your own portfolio names from myFund.pl
PORTFOLIOS = ["Główny", "IKE", "IKZE", "PPK"]

BASE_PATH = Path(__file__).parent.parent
GET_PORTFOLIO_PATH = Path(__file__).parent / "get_portfolio.py"
HISTORY_PATH = Path(__file__).parent.parent / "portfolios_history.json"
HISTORY_LIMIT = 8

def fetch_portfolio_value(name: str):
    cmd = ["python", "-X", "utf8", str(GET_PORTFOLIO_PATH), "--portfel", name, "--format", "json"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True, cwd=str(BASE_PATH), env={**os.environ})
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

def _empty_history():
    return {portfolio: {} for portfolio in PORTFOLIOS}


def _is_valid_day(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False
    return parsed.isoformat() == value


def _is_valid_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _normalize_portfolio_history(values):
    """Return only valid date -> numeric value entries from the v2 model."""
    if not isinstance(values, dict):
        # The old model used lists. Legacy values are intentionally discarded.
        return {}

    normalized = {}
    for day, value in values.items():
        if _is_valid_day(day) and _is_valid_number(value):
            normalized[day] = float(value)
    return dict(sorted(normalized.items()))


def load_history(path: Path):
    """Load the date-keyed history; unknown/legacy data starts as an empty state."""
    history = _empty_history()
    if not path.exists():
        return history

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw_history = json.load(f)
    except (OSError, json.JSONDecodeError):
        return history

    if not isinstance(raw_history, dict):
        return history

    # Keep configured portfolios and any already-recorded portfolio names. A
    # legacy list is normalized to {}, so it is replaced on the next save.
    for portfolio, values in raw_history.items():
        history[portfolio] = _normalize_portfolio_history(values)
    return history


def _prune_portfolio_history(values):
    if len(values) <= HISTORY_LIMIT:
        return
    dates = sorted(values)
    for day in dates[:-HISTORY_LIMIT]:
        del values[day]


def save_history(path: Path, history: dict):
    """Persist history atomically and retain only the latest eight dates."""
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized_history = {}
    for portfolio, values in history.items():
        normalized = _normalize_portfolio_history(values)
        _prune_portfolio_history(normalized)
        normalized_history[portfolio] = normalized

    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            json.dump(normalized_history, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.write("\n")
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def record_value(history: dict, portfolio: str, day: date, value: float):
    """Upsert one successful observation and prune older observations."""
    if not _is_valid_number(value):
        return False

    portfolio_history = history.setdefault(portfolio, {})
    if not isinstance(portfolio_history, dict):
        portfolio_history = {}
        history[portfolio] = portfolio_history

    day_key = day.isoformat()
    numeric_value = float(value)
    changed = portfolio_history.get(day_key) != numeric_value
    portfolio_history[day_key] = numeric_value
    before_prune = set(portfolio_history)
    _prune_portfolio_history(portfolio_history)
    return changed or set(portfolio_history) != before_prune


def _percentage_change(current_value, previous_value):
    if not _is_valid_number(current_value) or not _is_valid_number(previous_value) or previous_value == 0:
        return None
    return ((current_value - previous_value) / previous_value) * 100


def calculate_daily_change(history: dict, portfolio: str, day: date):
    values = history.get(portfolio, {})
    if not isinstance(values, dict):
        return None
    current = values.get(day.isoformat())
    previous = values.get((day - timedelta(days=1)).isoformat())
    return _percentage_change(current, previous)


def calculate_weekly_change(history: dict, portfolio: str, day: date):
    values = history.get(portfolio, {})
    if not isinstance(values, dict):
        return None
    current = values.get(day.isoformat())
    seven_days_ago = values.get((day - timedelta(days=7)).isoformat())
    return _percentage_change(current, seven_days_ago)


def generate_summary(today: date, history_path: Path, portfolios, fetcher):
    history = load_history(history_path)
    report_lines = []
    report_lines.append(f"Daily portfolio summary for {today.isoformat()}")
    report_lines.append("")

    current_values = {}
    daily_changes = {}
    weekly_changes = {}
    history_changed = False

    for port in portfolios:
        try:
            val = fetcher(port)
        except Exception as exc:
            print(f"Error fetching portfolio '{port}': {exc}", file=sys.stderr)
            val = None
        current_values[port] = val
        if val is not None and _is_valid_number(val):
            history_changed = record_value(history, port, today, val) or history_changed

    if history_changed:
        save_history(history_path, history)

    for port in portfolios:
        if current_values[port] is not None and _is_valid_number(current_values[port]):
            daily_changes[port] = calculate_daily_change(history, port, today)
            weekly_changes[port] = calculate_weekly_change(history, port, today)
        else:
            daily_changes[port] = None
            weekly_changes[port] = None

    for port in portfolios:
        val = current_values[port]
        if val is None or not _is_valid_number(val):
            report_lines.append(f"{port}: ERROR - data unavailable")
            continue
        daily_pct = daily_changes.get(port)
        daily_str = f"{daily_pct:.2f}%" if isinstance(daily_pct, float) else "-"
        wk_pct = weekly_changes.get(port)
        wk_str = f"{wk_pct:.2f}%" if isinstance(wk_pct, float) else "-"
        report_lines.append(f"{port}:")
        report_lines.append(f"  Wartość: {val:.2f} PLN")
        report_lines.append(f"  Zmiana dzienna: {daily_str}")
        report_lines.append(f"  Trend tygodniowy (7d): {wk_str}")
        report_lines.append("")

    return "\n".join(report_lines)


def main():
    api_key = os.environ.get("MYFUND_API_KEY")
    if not api_key:
        print("ERROR: MYFUND_API_KEY is not set. Set it (e.g., export MYFUND_API_KEY=your_key) and rerun.", file=sys.stderr)
        sys.exit(2)

    print(generate_summary(date.today(), HISTORY_PATH, PORTFOLIOS, fetch_portfolio_value))

if __name__ == "__main__":
    main()
