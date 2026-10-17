"""Check readable citations against verified metadata and the single-topic rule."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('publications', Path(__file__).with_name('build-publications.py'))
pubs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pubs)


class Citations(unittest.TestCase):
    def test_all_entries_keep_one_topic_and_include_doi(self):
        for paper in pubs.records + pubs.member_records:
            with self.subTest(doi=paper['doi']):
                pubs.validate(paper)
                self.assertEqual(len(paper['topics']), 1)
                text = pubs.plain_citation(paper)
                for value in [paper['authors'][0]['family'], str(paper['year']), paper['title'].rstrip('.'), paper['journal'], 'https://doi.org/' + paper['doi']]:
                    self.assertIn(value, text)
                self.assertNotIn('Published online', text)

    def test_readable_example_and_missing_volume(self):
        paper = next(p for p in pubs.records if p['doi'] == '10.1111/faf.70077')
        text = pubs.plain_citation(paper)
        self.assertIn('Punt, A. E.', text)
        self.assertIn('Fish and Fisheries, 27(3), 695–711.', text)
        sparse = dict(paper, authors=[paper['authors'][0]], volume='', issue='', pages='', article_number='')
        self.assertTrue(pubs.plain_citation(sparse).startswith('Wang, R. (2026).'))
        self.assertNotIn(', .', pubs.plain_citation(sparse))


if __name__ == '__main__':
    unittest.main()
