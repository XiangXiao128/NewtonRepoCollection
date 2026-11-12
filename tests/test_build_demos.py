import re
import subprocess
import sys
import tempfile
import time
import unittest
from html.parser import HTMLParser
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'build_demos.py'


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.groups = 0
        self.sources = []
        self.videos = []
        self.text = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'article':
            self.groups += 1
        if tag == 'source':
            self.sources.append(attrs['src'])
        if tag == 'video':
            self.videos.append(attrs)

    def handle_data(self, data):
        self.text.append(data)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.group = self.root / 'demos_isaac' / 'demo01'
        self.group.mkdir(parents=True)
        (self.group / '01.mp4').write_bytes(b'video fixture')
        (self.group / 'clip two.mp4').write_bytes(b'video fixture')
        newton = self.root / 'demos_newton' / 'demo01'
        newton.mkdir(parents=True)
        (newton / '01.mp4').write_bytes(b'video fixture')

    def build(self, success=True):
        result = subprocess.run([sys.executable, str(SCRIPT), '--root', str(self.root)],
                                capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def page(self):
        return self.root / 'documents' / 'demos_isaac.html'

    def test_initial_build_groups_videos_and_creates_metadata(self):
        self.build()
        info = (self.group / 'info.md').read_text()
        self.assertIn('## Software Version', info)
        self.assertIn('## Author Homepage', info)
        self.assertIn('## Author Email', info)
        self.assertIn('| clip two | clip two.mp4 |', info)
        page = Page(self.page().read_text())
        self.assertEqual(page.groups, 1)
        self.assertEqual(page.sources, ['../demos_isaac/demo01/01.mp4',
                                        '../demos_isaac/demo01/clip%20two.mp4'])
        self.assertEqual(Page((self.root / 'documents/demos_newton.html').read_text()).groups, 1)

    def test_info_edits_sync_text_name_order_and_preserve_input(self):
        self.build()
        info = self.group / 'info.md'
        edited = '''# Demo Information

## Name
Robot & Object

## Description
A shared description.

## Software Version
Simulator 5.0

## Source Repository
https://example.com/source

## Author
Alice <Team>

## Videos
| Name | Path |
| --- | --- |
| Second angle | clip two.mp4 |
| First angle | 01.mp4 |
'''
        info.write_text(edited)
        self.build()
        page = Page(self.page().read_text())
        text = ''.join(page.text)
        for value in ['Robot & Object', 'A shared description.', 'Simulator 5.0', 'Alice <Team>', 'Second angle']:
            self.assertIn(value, text)
        self.assertEqual(page.sources[0], '../demos_isaac/demo01/clip%20two.mp4')
        self.assertEqual(info.read_text(), edited)
        self.assertIn('href="https://example.com/source"', self.page().read_text())

    def test_initial_video_autoplays_muted_and_all_videos_loop_inline(self):
        self.build()
        videos = Page(self.page().read_text()).videos
        self.assertIn('autoplay', videos[0])
        self.assertNotIn('autoplay', videos[1])
        for video in videos:
            for attribute in ('muted', 'loop', 'playsinline', 'controls'):
                self.assertIn(attribute, video)

    def test_description_renders_bold_text_and_escapes_html(self):
        self.build()
        info = self.group / 'info.md'
        description = 'Using **MujocoSolver and VBD**, plus **A & B** and <em>plain text</em>. **unfinished'
        text = re.sub(r'(?m)^## Description\n.*?(?=^## )', '## Description\n' + description + '\n\n', info.read_text(), flags=re.S)
        info.write_text(text)
        self.build()
        html = self.page().read_text()
        self.assertIn('<strong>MujocoSolver and VBD</strong>', html)
        self.assertIn('<strong>A &amp; B</strong>', html)
        self.assertIn('&lt;em&gt;plain text&lt;/em&gt;', html)
        self.assertIn('**unfinished', html)
        self.assertIn(description, info.read_text())

    def test_author_name_links_to_homepage_or_email_without_extra_rows(self):
        self.build()
        info = self.group / 'info.md'
        base = info.read_text().replace('## Author\n', '## Author\nLixin Xu\n')
        # Start from the legacy headings so optional fields remain backward compatible.
        base = re.sub(r'## Author (?:Homepage|Email)\n.*?(?=\n## )', '', base, flags=re.S)
        cases = [
            ('davidlxu.github.io', '', '<a href="https://davidlxu.github.io">Lixin Xu</a>'),
            ('https://davidlxu.github.io', 'author@example.com', '<a href="https://davidlxu.github.io">Lixin Xu</a>'),
            ('', 'author@example.com', '<a href="mailto:author@example.com">Lixin Xu</a>'),
            ('', '', '<dd>Lixin Xu</dd>'),
        ]
        for homepage, email, expected in cases:
            with self.subTest(homepage=homepage, email=email):
                contacts = f'## Author Homepage\n{homepage}\n\n## Author Email\n{email}\n\n'
                info.write_text(base.replace('## Videos', contacts + '## Videos'))
                self.build()
                html = self.page().read_text()
                self.assertIn(expected, html)
                self.assertEqual(html.count('<dt>'), 4)

    def test_invalid_author_homepage_preserves_generated_page(self):
        self.build()
        original = self.page().read_bytes()
        info = self.group / 'info.md'
        # Replace the section if the template already includes it.
        text = re.sub(r'## Author Homepage\n.*?(?=\n## )', '', info.read_text(), flags=re.S)
        info.write_text(text.replace('## Videos', '## Author Homepage\njavascript:alert(1)\n\n## Videos'))
        result = self.build(success=False)
        self.assertIn('Author Homepage', result.stderr)
        self.assertEqual(self.page().read_bytes(), original)

    def test_multiple_authors_have_individual_homepage_and_email_links(self):
        self.build()
        info = self.group / 'info.md'
        authors = '''## Author
| Name | Homepage | Email |
| --- | --- | --- |
| Qiwei Wu | nathanwu7.github.io | |
| Fangyuan Shi | | fangyuanshi2006@gmail.com |
| Baijun Chen | byml-c.github.io | |

'''
        info.write_text(re.sub(r'(?m)^## Author\n.*?(?=^## )', authors, info.read_text(), flags=re.S))
        self.build()
        html = self.page().read_text()
        expected = ('<a href="https://nathanwu7.github.io">Qiwei Wu</a>, '
                    '<a href="mailto:fangyuanshi2006@gmail.com">Fangyuan Shi</a>, '
                    '<a href="https://byml-c.github.io">Baijun Chen</a>')
        self.assertIn('<dt>Author</dt><dd>' + expected + '</dd>', html)
        self.assertEqual(html.count('<dt>'), 4)

    def test_invalid_video_path_preserves_existing_html(self):
        self.build()
        original = self.page().read_bytes()
        info = self.group / 'info.md'
        info.write_text(info.read_text().replace('01.mp4', 'missing.mp4'))
        result = self.build(success=False)
        self.assertIn('missing.mp4', result.stderr)
        self.assertEqual(self.page().read_bytes(), original)

    def test_watch_rebuilds_after_info_is_saved(self):
        self.build()
        log = self.root / 'watch.log'
        output = log.open('w')
        self.addCleanup(output.close)
        proc = subprocess.Popen([sys.executable, str(SCRIPT), '--root', str(self.root), '--watch'],
                                stdout=output, stderr=output)
        self.addCleanup(lambda: self.stop(proc))
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline and 'Watching demo folders.' not in log.read_text():
            time.sleep(0.05)
        self.assertIn('Watching demo folders.', log.read_text())
        info = self.group / 'info.md'
        info.write_text(info.read_text().replace('## Description', '## Description\nSaved during watch.'))
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            if 'Saved during watch.' in self.page().read_text():
                break
            time.sleep(0.1)
        self.assertIn('Saved during watch.', self.page().read_text())

    @staticmethod
    def stop(proc):
        proc.terminate()
        proc.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
