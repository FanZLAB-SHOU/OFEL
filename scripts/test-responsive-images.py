"""Check responsive rewriting, fallback safety, and nested-page asset URLs."""
import unittest
from unittest.mock import patch
from responsive_images import responsive_images
from site_paths import rebase_links


class ResponsiveImages(unittest.TestCase):
    def setUp(self):
        self.source = 'assets/people/example.jpg'
        entry = {'width': 1600, 'height': 1200, 'sha256': 'test', 'variants': [
            {'width': w, 'src': f'assets/optimized/example-{w}.webp'} for w in [320, 640, 960, 1600]]}
        self.mapping = patch('responsive_images.manifest', return_value={self.source: entry})
        self.valid = patch('responsive_images.current', return_value=True)
        self.mapping.start(); self.valid.start()
        self.addCleanup(self.mapping.stop); self.addCleanup(self.valid.stop)

    def test_preserves_description_crop_and_source_attribution(self):
        source = f'<img src="{self.source}" class="gateway-bg" alt="A &amp; B" width="1536" height="1024" loading="lazy" style="object-position:70% 50%">'
        result = responsive_images(source)
        for text in ['alt="A &amp; B"', 'loading="lazy"', 'object-position:70% 50%', 'width="1600"',
                     'height="1200"', 'example-960.webp', 'example-320.webp 320w', 'max(84vw, 693px)',
                     f'data-image-original="{self.source}"']:
            self.assertIn(text, result)
        self.assertEqual(responsive_images(result), result)

    def test_small_portraits_and_explicit_sizes(self):
        result = responsive_images(f'<img class="member-photo" src="{self.source}">')
        self.assertIn('sizes="(max-width: 700px) 90px, 108px"', result)
        result = responsive_images(f'<img src="{self.source}" sizes="320px">')
        self.assertEqual(result.count('sizes='), 1)
        self.assertIn('sizes="320px"', result)

    def test_changed_sources_fall_back_to_original(self):
        source = f'<img src="{self.source}" alt="Updated portrait">'
        with patch('responsive_images.current', return_value=False):
            self.assertEqual(responsive_images(source), source)
        unknown = '<img src="assets/new-photo.png" alt="New photo">'
        self.assertEqual(responsive_images(unknown), unknown)

    def test_existing_srcset_and_external_images_are_untouched(self):
        for source in [f'<img src="{self.source}" srcset="small.webp 320w, large.webp 960w">',
                       '<img src="https://example.org/photo.png">']:
            self.assertEqual(responsive_images(source), source)

    def test_nested_pages_keep_all_variants_relative(self):
        result = rebase_links(responsive_images(f'<img src="{self.source}">'), 'members/example/index.html')
        self.assertIn('src="../../assets/optimized/example-960.webp"', result)
        self.assertIn('srcset="../../assets/optimized/example-320.webp 320w', result)
        self.assertIn('../../assets/optimized/example-1600.webp 1600w', result)


if __name__ == '__main__':
    unittest.main()
