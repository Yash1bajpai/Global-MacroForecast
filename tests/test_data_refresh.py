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


class WiringTests(unittest.TestCase):
    root = __import__('pathlib').Path(__file__).resolve().parents[1]

    def test_frozen_fred_ids_are_not_fetched(self):
        text = (self.root / 'config/settings.py').read_text(encoding='utf-8')
        for frozen in ('JPNCPIALLMINMEI', 'JPNPROINDMISMEI', 'DEUPROINDQISMEI', 'INDCPIALLMINMEI', 'DEUCPIALLMINMEI'):
            self.assertNotIn(f'"{frozen}"', text)

    def test_monthly_workflow_is_fail_closed_and_refreshes_before_preprocess(self):
        wf = (self.root / '.github/workflows/auto_update.yml').read_text(encoding='utf-8')
        self.assertLess(wf.index('src.data.fetch_oecd_sdmx'), wf.index('preprocess.py'))
        self.assertLess(wf.index('preprocess.py'), wf.index('src.data.freshness'))
        self.assertLess(wf.index('src.data.freshness'), wf.index('train_candidate'))
        self.assertIn('contents: read', wf)
        code = '\n'.join(l for l in wf.lower().splitlines() if not l.strip().startswith('#'))
        for forbidden in ('git push', 'contents: write', 'vercel', 'render', 'deploy'):
            self.assertNotIn(forbidden, code)

    def test_availability_reports_gaps_and_origin_share(self):
        from src.data.freshness import availability_report
        idx = pd.date_range('2010-01-01', periods=20, freq='QS')
        m = pd.DataFrame({'gdp_growth': 1.0, 'cpi_level': 100.0}, index=idx)
        m.loc[idx[5], 'cpi_level'] = np.nan
        r = availability_report(m)['cpi_level']
        self.assertEqual(r['missing_quarters'], ['2011-Q2'])
        self.assertAlmostEqual(r['origin_availability'], 17 / 20)  # t-2 missing at the first two origins and at index 7


class RefreshIdempotenceTests(unittest.TestCase):
    def test_refresh_twice_and_against_quarterly_legacy(self):
        import tempfile
        from pathlib import Path
        from src.data import fetch_oecd_sdmx as f
        idx = pd.period_range('2000-01', periods=120, freq='M')
        vals = 100 + np.cumsum(np.sin(np.arange(120)))
        payload = 'TIME_PERIOD,OBS_VALUE\n' + '\n'.join(f'{p},{v}' for p, v in zip(idx.astype(str), vals))
        spec = {('germany', 'indpro'): ('flow', 'key', 'test')}
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'germany').mkdir()
            # quarterly legacy file (means of complete quarters)
            s = pd.Series(vals, index=idx.to_timestamp())
            q = s.resample('QS').mean()
            q.rename('value').rename_axis('date').reset_index().to_csv(Path(d) / 'germany/indpro.csv', index=False)
            f.refresh(d, spec, fetcher=lambda *a: payload)      # replaces quarterly legacy file
            f.refresh(d, spec, fetcher=lambda *a: payload)      # now compares against monthly file
            out = pd.read_csv(Path(d) / 'germany/indpro.csv')
            self.assertEqual(len(out), 120)


class LeadingIndexTests(unittest.TestCase):
    def test_leading_index_is_country_specific_and_skips_contaminated_baseline(self):
        import tempfile, json
        from pathlib import Path
        from src.data import fetch_oecd_sdmx as f
        jp, de = f.SPECS[('japan', 'oecd_leading_index')], f.SPECS[('germany', 'oecd_leading_index')]
        self.assertTrue(jp[1].startswith('JPN.') and de[1].startswith('DEU.'))
        self.assertEqual(jp[1].split('.', 1)[1], de[1].split('.', 1)[1])
        self.assertIn('.LI.', jp[1])
        self.assertIn('.AA.', jp[1])

        def fake(flow, key):
            base = 100.0 if key.startswith('JPN') else 90.0
            rows = ''.join(f'{p},{base + i}\n' for i, p in enumerate(pd.period_range('2000-01', '2026-08', freq='M').astype(str)))
            return 'TIME_PERIOD,OBS_VALUE\n' + rows

        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            for c in ('japan', 'germany'):
                (d / c).mkdir()
                # contaminated legacy file: many values per date
                (d / c / 'oecd_leading_index.csv').write_text('date,value\n2015-01-01,1\n2015-01-01,200\n', encoding='utf-8')
            f.refresh(d, {k: v for k, v in f.SPECS.items() if k[1] == 'oecd_leading_index'}, fake)
            a = pd.read_csv(d / 'japan' / 'oecd_leading_index.csv'); b = pd.read_csv(d / 'germany' / 'oecd_leading_index.csv')
            self.assertFalse(a.date.duplicated().any())
            self.assertFalse(a.equals(b))
            src = json.loads((d / 'SOURCES.json').read_text(encoding='utf-8'))
            self.assertIn('replaced_file_note', src['japan/oecd_leading_index'])
