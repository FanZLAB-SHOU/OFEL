"""Check readable citations against verified metadata and the single-topic rule."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('publications', Path(__file__).with_name('build-publications.py'))
pubs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pubs)


class Citations(unittest.TestCase):
    def test_all_entries_keep_one_topic_and_include_verified_link(self):
        for paper in pubs.records + pubs.member_records:
            with self.subTest(doi=paper['doi']):
                pubs.validate(paper)
                self.assertEqual(len(paper['topics']), 1)
                text = pubs.plain_citation(paper)
                first = paper['authors'][0]
                name = first.get('name_zh') if paper.get('language') == 'zh-CN' else first['family']
                link = 'https://doi.org/' + paper['doi'] if paper.get('doi') else paper['source']
                for value in [name, str(paper['year']), paper['title'].rstrip('.'), paper['journal'], link]:
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

    def test_chinese_citations_and_no_doi_export(self):
        paper = next(p for p in pubs.member_records if p['title'].startswith('基于环境因子的日本鲭'))
        self.assertFalse(paper['doi'])
        self.assertIn('林琴琴, 陈新军, & 戴黎斌 (2018)', pubs.plain_citation(paper))
        bib = pubs.citation(paper)
        self.assertIn('author = {{林琴琴} and {陈新军} and {戴黎斌}}', bib)
        self.assertIn('url = {' + paper['source'] + '}', bib)
        self.assertNotIn('doi =', bib)

    def test_lab_rule_and_unique_all_collection(self):
        papers = pubs.page_records()
        self.assertEqual(len(papers), len(pubs.records) + len(pubs.member_records))
        self.assertEqual(len(papers), len({pubs.paper_key(p) for p in papers}))
        review = next(p for p in papers if p['doi'] == '10.13984/j.cnki.cn37-1141.2025.06.033')
        self.assertTrue(pubs.is_lab_paper(review), 'Any author position counts for the Lab collection')
        self.assertFalse(pubs.has_lab_first_author(review), 'External first authors stay out of the mentor selection')
        lin = next(p for p in papers if p['doi'] == '10.12024/jsou.20220303745')
        self.assertFalse(pubs.is_lab_paper(lin), 'Member authorship alone is not lab attribution')
        self.assertNotIn('Lab research', pubs.article_html(lin))

    def test_chinese_alias_searches_english_records(self):
        paper = next(p for p in pubs.member_records if p['doi'] == '10.1111/1365-2664.70572')
        self.assertIn('唐茹彤', pubs.article_html(paper))
        self.assertNotIn('唐如彤', pubs.article_html(paper))

    def test_confirmed_external_collaboration_overrides_lab_coauthors(self):
        paper = next(p for p in pubs.records if p['doi'] == '10.1111/faf.70015')
        self.assertTrue(pubs.has_fan_zhang(paper))
        self.assertIn(paper, pubs.page_records())
        self.assertFalse(pubs.is_lab_paper(paper))
        rendered = pubs.article_html(paper)
        self.assertIn('External collaboration', rendered)
        self.assertNotIn('Lab research', rendered)
        self.assertIn('data-lab="false"', rendered)
        self.assertNotIn(paper['doi'], (pubs.ROOT / 'assets/lab-publications.bib').read_text())
        self.assertIn(paper['doi'], (pubs.ROOT / 'assets/all-publications.bib').read_text())
        self.assertIn(paper['doi'], (pubs.ROOT / 'assets/selected-publications.bib').read_text())

    def test_accepted_paper_is_not_presented_as_published_online(self):
        paper = next(p for p in pubs.member_records if p.get('status') == 'accepted')
        pubs.validate(paper)
        self.assertIn('Accepted · 2026-04-16', pubs.article_html(paper))
        self.assertNotIn('Published online', pubs.article_html(paper))
        self.assertIn('Accepted 2026-04-16', pubs.plain_citation(paper))
        self.assertIn('publication date not yet assigned', pubs.citation(paper))
        self.assertNotIn('doi =', pubs.citation(paper))
        self.assertTrue(pubs.is_lab_paper(paper))


if __name__ == '__main__':
    unittest.main()
