"""Regression checks for clean URLs, legacy routes, and nested asset references."""

import unittest
from site_paths import BASE, clean_url, legacy_routes, output_path, rebase_links, source_paths


class SitePaths(unittest.TestCase):
    def test_public_directory_urls(self):
        cases = {
            'index.html': '',
            'members/index.html': 'members/',
            'members/fan-zhang.html': 'members/fan-zhang/',
            'news/2026-04-mse-course.html': 'news/2026-04-mse-course/',
            'resources/reference-materials.html': 'resources/reference-materials/',
            'publications.html': 'publications/',
            'research.html': 'research/themes/',
            'blog.html': 'news/',
            'fan-zhang.html': 'members/fan-zhang/',
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(clean_url(source), expected)
                self.assertEqual(output_path(source), expected + 'index.html')

    def test_directory_outputs_are_stable(self):
        for source in source_paths():
            destination = output_path(source)
            self.assertEqual(output_path(destination), destination)
        self.assertEqual(output_path('404.html'), '404.html')
        self.assertEqual(len({output_path(p) for p in source_paths()}), len(source_paths()))

    def test_deep_links_assets_and_query_fragments(self):
        source = ('<a href="index.html">Home</a><a href="publications.html?view=all&amp;from=profile#publications-fan-zhang">Papers</a>'
                  '<a href="members/index.html">People</a><img src="assets/people/fan-zhang.jpg">'
                  '<script src="script.js?v=abcd"></script><a href="#local">Section</a>')
        actual = rebase_links(source, 'members/fan-zhang/index.html')
        for expected in ['href="../../"', 'href="../../publications/?view=all&amp;from=profile#publications-fan-zhang"',
                         'href="../"', 'src="../../assets/people/fan-zhang.jpg"', 'src="../../script.js?v=abcd"', 'href="#local"']:
            self.assertIn(expected, actual)

    def test_external_urls_and_absolute_canonicals(self):
        markup = f'<a href="https://example.org/page.html">External</a><a href="mailto:a@example.org">Email</a><link href="{BASE}members/fan-zhang.html">'
        actual = rebase_links(markup, 'news/example/index.html')
        self.assertIn('href="https://example.org/page.html"', actual)
        self.assertIn('href="mailto:a@example.org"', actual)
        self.assertIn(f'href="{BASE}members/fan-zhang/"', actual)

    def test_srcset_keeps_descriptors(self):
        actual = rebase_links('<img srcset="assets/small.png 480w, assets/large.png 960w">', 'research/themes/index.html')
        self.assertEqual(actual, '<img srcset="../../assets/small.png 480w, ../../assets/large.png 960w">')

    def test_legacy_aliases_point_directly_to_directory_urls(self):
        routes = legacy_routes()
        self.assertEqual(routes['fan-zhang.html'], routes['members/fan-zhang.html'])
        self.assertEqual(routes['news-2026-04-mse-course.html'], routes['news/2026-04-mse-course.html'])
        for source, target in routes.items():
            self.assertTrue(source.endswith('.html'))
            self.assertTrue(not target or target.endswith('/'))
            self.assertNotIn('.html', target)


if __name__ == '__main__':
    unittest.main()
