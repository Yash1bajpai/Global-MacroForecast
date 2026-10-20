"""Source refresh, partial-quarter and stale-input checks (offline)."""
import unittest
import numpy as np
import pandas as pd
from src.data.fetch_oecd_sdmx import parse_sdmx_csv, continuity_report, check_continuity
from src.data.freshness import freshness_report, stale_columns
from src.data.preprocess import to_quarterly

CSV = 'DATAFLOW,REF_AREA,TIME_PERIOD,OBS_VALUE,OBS_STATUS\nX,JPN,2026-01,100.5,A\nX,JPN,2025-12,100.0,A\n'


class RefreshTests(unittest.TestCase):
    def test_parse_sorts_and_types(self):
        s = parse_sdmx_csv(CSV)
        self.assertEqual(list(s.index), [pd.Timestamp('2025-12-01'), pd.Timestamp('2026-01-01')])
        self.assertEqual(s.iloc[-1], 100.5)

    def test_parse_rejects_duplicate_periods_and_bad_payload(self):
        with self.assertRaises(ValueError):
            parse_sdmx_csv(CSV + 'X,JPN,2026-01,101,A\n')
        with self.assertRaises(ValueError):
            parse_sdmx_csv('<html>error</html>\n')

    def _series(self, n=60, scale=1.0):
        idx = pd.date_range('2015-01-01', periods=n, freq='MS')
        return pd.Series(100 + np.cumsum(np.sin(np.arange(n))) , index=idx) * scale

    def test_continuity_accepts_same_series_and_rejects_different_one(self):
        old = self._series()
        check_continuity(continuity_report(old * 1.001, old))
        with self.assertRaises(ValueError):
            check_continuity(continuity_report(old * 1.2, old))
        other = pd.Series(np.random.default_rng(0).normal(100, 5, len(old)), index=old.index)
        with self.assertRaises(ValueError):
            check_continuity(continuity_report(other, old))

    def test_continuity_requires_enough_overlap(self):
        old = self._series(12)
        with self.assertRaises(ValueError):
            continuity_report(old, old)

    def test_partial_quarter_is_missing_not_averaged(self):
        s = pd.Series([1., 2., 3., 4., 5.], index=pd.to_datetime(['2025-01-01', '2025-02-01', '2025-03-01', '2025-04-01', '2025-06-01']))
        q = to_quarterly(s)
        self.assertEqual(q[pd.Timestamp('2025-01-01')], 2.0)
        self.assertTrue(np.isnan(q[pd.Timestamp('2025-04-01')]))

    def test_freshness_flags_stale_columns(self):
        idx = pd.date_range('2020-01-01', periods=10, freq='QS')
        m = pd.DataFrame({'gdp_growth': 1.0, 'cpi_level': 100.0, 'indpro_level': 100.0}, index=idx)
        m.loc[idx[4]:, 'cpi_level'] = np.nan
        self.assertEqual(stale_columns(m), ['cpi_level'])
        self.assertEqual(freshness_report(m)['indpro_level']['lag_quarters'], 0)


if __name__ == '__main__':
    unittest.main()
