import re

from django.test import TestCase
from django.urls import reverse


class HomePageTests(TestCase):
    def test_home_hero_content_is_wrapped_in_hero_section(self):
        response = self.client.get(reverse('core:home'))

        self.assertEqual(response.status_code, 200)

        html = response.content.decode()
        pattern = (
            r'<section class="tx-hero"[^>]*>\s*'
            r'<div class="tx-hero-inner">.*?'
            r'TOMMY<span style="color:var\(--tx-orange\)">\.X</span>.*?'
            r'</div>\s*</section>'
        )
        self.assertRegex(html, pattern)
