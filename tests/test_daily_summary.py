import contextlib
import io
import importlib.util
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "myfund-portfolio" / "scripts" / "daily_summary.py"
SPEC = importlib.util.spec_from_file_location("daily_summary", SCRIPT_PATH)
daily_summary = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(daily_summary)


class DailySummaryHistoryTests(unittest.TestCase):
    PORTFOLIO = "Główny"

    def test_same_day_is_upserted_and_not_appended(self):
        history = {self.PORTFOLIO: {}}
        first_day = date(2026, 8, 19)
        current_day = date(2026, 8, 20)

        self.assertTrue(daily_summary.record_value(history, self.PORTFOLIO, first_day, 100.0))
        self.assertTrue(daily_summary.record_value(history, self.PORTFOLIO, current_day, 110.0))
        self.assertTrue(daily_summary.record_value(history, self.PORTFOLIO, current_day, 120.0))

        self.assertEqual(history[self.PORTFOLIO], {
            "2026-08-19": 100.0,
            "2026-08-20": 120.0,
        })
        self.assertAlmostEqual(
            daily_summary.calculate_daily_change(history, self.PORTFOLIO, current_day),
            20.0,
        )

    def test_generate_summary_persists_same_day_update(self):
        first_day = date(2026, 8, 19)
        current_day = date(2026, 8, 20)
        with tempfile.TemporaryDirectory() as directory:
            history_path = Path(directory) / "portfolios_history.json"

            daily_summary.generate_summary(
                first_day,
                history_path,
                [self.PORTFOLIO],
                lambda _portfolio: 100.0,
            )
            daily_summary.generate_summary(
                current_day,
                history_path,
                [self.PORTFOLIO],
                lambda _portfolio: 110.0,
            )
            report = daily_summary.generate_summary(
                current_day,
                history_path,
                [self.PORTFOLIO],
                lambda _portfolio: 120.0,
            )

            saved = json.loads(history_path.read_text(encoding="utf-8"))
            self.assertEqual(saved[self.PORTFOLIO], {
                "2026-08-19": 100.0,
                "2026-08-20": 120.0,
            })
            self.assertIn("Zmiana dzienna: 20.00%", report)

    def test_missing_day_does_not_become_zero_or_previous_observation(self):
        current_day = date(2026, 8, 20)
        history = {
            self.PORTFOLIO: {
                "2026-08-18": 100.0,
                "2026-08-20": 120.0,
            }
        }

        self.assertNotIn("2026-08-19", history[self.PORTFOLIO])
        self.assertIsNone(
            daily_summary.calculate_daily_change(history, self.PORTFOLIO, current_day)
        )
        self.assertIsNone(
            daily_summary.calculate_weekly_change(history, self.PORTFOLIO, current_day)
        )

    def test_weekly_change_uses_exact_calendar_date(self):
        current_day = date(2026, 8, 20)
        history = {
            self.PORTFOLIO: {
                (current_day - timedelta(days=7)).isoformat(): 100.0,
                current_day.isoformat(): 107.0,
            }
        }

        self.assertAlmostEqual(
            daily_summary.calculate_weekly_change(history, self.PORTFOLIO, current_day),
            7.0,
        )

    def test_only_last_eight_unique_dates_are_retained(self):
        history = {self.PORTFOLIO: {}}
        first_day = date(2026, 8, 1)

        for offset in range(9):
            daily_summary.record_value(
                history,
                self.PORTFOLIO,
                first_day + timedelta(days=offset),
                float(offset + 1),
            )

        values = history[self.PORTFOLIO]
        self.assertEqual(len(values), 8)
        self.assertNotIn("2026-08-01", values)
        self.assertIn("2026-08-02", values)
        self.assertIn("2026-08-09", values)

    def test_failed_fetch_does_not_write_a_sample(self):
        current_day = date(2026, 8, 20)
        with tempfile.TemporaryDirectory() as directory:
            history_path = Path(directory) / "portfolios_history.json"
            daily_summary.save_history(
                history_path,
                {self.PORTFOLIO: {"2026-08-19": 100.0}},
            )
            before = history_path.read_text(encoding="utf-8")

            report = daily_summary.generate_summary(
                current_day,
                history_path,
                [self.PORTFOLIO],
                lambda _portfolio: None,
            )

            self.assertIn("Główny: ERROR - data unavailable", report)
            self.assertEqual(history_path.read_text(encoding="utf-8"), before)
            saved = json.loads(before)
            self.assertNotIn("2026-08-20", saved[self.PORTFOLIO])

    def test_fetch_exception_does_not_write_a_sample(self):
        current_day = date(2026, 8, 20)
        with tempfile.TemporaryDirectory() as directory:
            history_path = Path(directory) / "portfolios_history.json"

            def failing_fetch(_portfolio):
                raise RuntimeError("network unavailable")

            with contextlib.redirect_stderr(io.StringIO()):
                report = daily_summary.generate_summary(
                    current_day,
                    history_path,
                    [self.PORTFOLIO],
                    failing_fetch,
                )

            self.assertIn("Główny: ERROR - data unavailable", report)
            self.assertFalse(history_path.exists())

    def test_legacy_list_is_treated_as_empty_state(self):
        with tempfile.TemporaryDirectory() as directory:
            history_path = Path(directory) / "portfolios_history.json"
            history_path.write_text(
                json.dumps({self.PORTFOLIO: [0.0, 100.0]}),
                encoding="utf-8",
            )

            history = daily_summary.load_history(history_path)

            self.assertEqual(history[self.PORTFOLIO], {})


if __name__ == "__main__":
    unittest.main()
