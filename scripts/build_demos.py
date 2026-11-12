#!/usr/bin/env python3
"""Build standalone demo galleries from each group's info.md (Python 3.9+)."""

import argparse
import os
import re
import sys
import time
from html import escape
from pathlib import Path
from urllib.parse import quote, urlsplit


REPO = Path(__file__).resolve().parents[1]
KINDS = ('isaac', 'newton')
VIDEO_TYPES = {'.mp4': 'video/mp4', '.webm': 'video/webm', '.mov': 'video/quicktime', '.m4v': 'video/mp4'}
FIELDS = ('Name', 'Description', 'Software Version', 'Source Repository', 'Author', 'Videos')
CONTACT_FIELDS = ('Author Homepage', 'Author Email')


def video_files(folder):
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in VIDEO_TYPES)


def create_info(folder):
    """Initialize new groups only; never replace an author's metadata."""
    info = folder / 'info.md'
    if info.exists():
        return
    videos = video_files(folder)
    if not videos:
        return
    rows = '\n'.join('| {} | {} |'.format(v.stem, v.name) for v in videos)
    info.write_text(f'''# Demo Information

<!-- Edit the fields below, then run scripts/build_demos.py (or keep --watch running).
     Description supports **bold** text. Other text fields are plain text.
     Source Repository accepts an HTTP(S) URL.
     Video paths are relative to this info.md. Table row order controls slide order.
     Add or remove video rows when changing the group. -->

## Name
{folder.name}

## Description
<!-- Add a one-sentence description shared by all videos in this group. -->

## Software Version
<!-- Add the software name and version. -->

## Source Repository
<!-- Add the source repository URL. -->

## Author
<!-- Add the author's name. -->

## Author Homepage
<!-- Add a personal homepage URL. Used as the author's name link when provided. -->

## Author Email
<!-- Add an email address. Used as the author's name link when no homepage is provided. -->

## Videos
| Name | Path |
| --- | --- |
{rows}
''', encoding='utf-8')


def author_link(homepage, email, info):
    if homepage:
        if not urlsplit(homepage).scheme:
            homepage = 'https://' + homepage
        url = urlsplit(homepage)
        if url.scheme not in ('http', 'https') or not url.netloc or re.search(r'\s', homepage):
            raise ValueError(f'{info}: Author Homepage must be an HTTP(S) URL')
    if email and not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', email):
        raise ValueError(f'{info}: Author Email must be an email address')
    return homepage or ('mailto:' + quote(email, safe='@') if email else '')


def read_authors(data, info):
    if not data['Author'].startswith('|'):
        link = author_link(data['Author Homepage'], data['Author Email'], info)
        return [(data['Author'], link)] if data['Author'] else []
    authors = []
    for line in data['Author'].splitlines():
        if not line.strip():
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if cells == ['Name', 'Homepage', 'Email'] or all(re.fullmatch(r':?-{3,}:?', cell) for cell in cells):
            continue
        if len(cells) != 3 or not cells[0]:
            raise ValueError(f'{info}: each Author table row needs Name, Homepage, and Email cells')
        name, homepage, email = cells
        authors.append((name, author_link(homepage, email, info)))
    if not authors:
        raise ValueError(f'{info}: list at least one author in the Author table')
    return authors


def read_info(info):
    text = re.sub(r'<!--.*?-->', '', info.read_text(encoding='utf-8'), flags=re.S)
    sections = {}
    current = None
    for line in text.splitlines():
        if line.startswith('## '):
            current = line[3:].strip()
            if current not in FIELDS + CONTACT_FIELDS or current in sections:
                raise ValueError(f'{info}: unknown or duplicate heading {current!r}')
            sections[current] = []
        elif current:
            sections[current].append(line)
    if not set(FIELDS).issubset(sections):
        raise ValueError(f'{info}: required headings are {", ".join(FIELDS)}')
    data = {key: '\n'.join(value).strip() for key, value in sections.items()}
    for key in CONTACT_FIELDS:
        data.setdefault(key, '')
    data['Name'] = data['Name'] or info.parent.name
    if data['Source Repository']:
        url = urlsplit(data['Source Repository'])
        if url.scheme not in ('http', 'https') or not url.netloc:
            raise ValueError(f'{info}: Source Repository must be an HTTP(S) URL')
    data['authors'] = read_authors(data, info)
    videos = []
    seen = set()
    for line in sections['Videos']:
        if not line.strip():
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if cells == ['Name', 'Path'] or all(re.fullmatch(r':?-{3,}:?', cell) for cell in cells):
            continue
        if len(cells) != 2 or not all(cells):
            raise ValueError(f'{info}: each video row needs a Name and a Path')
        name, relative = cells
        path = (info.parent / relative).resolve()
        if (Path(relative).is_absolute() or info.parent.resolve() not in path.parents
                or not path.is_file() or path.suffix.lower() not in VIDEO_TYPES):
            raise ValueError(f'{info}: invalid or missing video path: {relative}')
        if path in seen:
            raise ValueError(f'{info}: duplicate video path: {relative}')
        seen.add(path)
        videos.append((name, path))
    if not videos:
        raise ValueError(f'{info}: list at least one video in the Videos table')
    data['videos'] = videos
    return data


def render_group(data, index, output_dir):
    slides = []
    for slide_index, (name, path) in enumerate(data['videos']):
        src = escape(quote(os.path.relpath(path, output_dir), safe='/'), quote=True)
        title = escape(name)
        slides.append(f'''          <figure class="slide">
            <video controls muted loop playsinline{' autoplay' if slide_index == 0 else ''} preload="{'metadata' if slide_index == 0 else 'none'}" aria-label="{title}">
              <source src="{src}" type="{VIDEO_TYPES[path.suffix.lower()]}">
              Your browser does not support embedded video. Use the link below.
            </video>
            <figcaption>{title} · <a href="{src}">Open video file</a></figcaption>
          </figure>''')
    rows = []
    for field in FIELDS[1:-1]:
        value = escape(data[field])
        if field == 'Description':
            value = re.sub(r'\*\*(\S(?:.*?\S)?)\*\*', r'<strong>\1</strong>', value)
        elif field == 'Source Repository' and value:
            value = f'<a href="{value}">{value}</a>'
        elif field == 'Author':
            value = ', '.join(
                f'<a href="{escape(link, quote=True)}">{escape(name)}</a>' if link else escape(name)
                for name, link in data['authors']
            )
        rows.append(f'        <div class="detail-row"><dt>{field}</dt><dd>{value}</dd></div>')
    count = len(slides)
    return f'''    <article class="demo-group" aria-labelledby="group-{index}-title">
      <h2 id="group-{index}-title">{escape(data['Name'])}</h2>
      <div class="demo-layout">
        <div class="video-panel">
          <div class="carousel" id="group-{index}-videos" tabindex="0" role="region" aria-roledescription="carousel" aria-label="{escape(data['Name'], quote=True)} videos">
{chr(10).join(slides)}
          </div>
          <div class="carousel-controls">
            <button type="button" data-direction="-1" aria-controls="group-{index}-videos" aria-label="Previous video" disabled>← Previous</button>
            <span class="slide-count" aria-live="polite" aria-atomic="true">1 / {count}</span>
            <button type="button" data-direction="1" aria-controls="group-{index}-videos" aria-label="Next video"{' disabled' if count == 1 else ''}>Next →</button>
          </div>
        </div>
        <dl class="details">
{chr(10).join(rows)}
        </dl>
      </div>
    </article>'''


def render_page(kind, groups, output_dir):
    other = 'newton' if kind == 'isaac' else 'isaac'
    articles = '\n'.join(render_group(data, i, output_dir) for i, data in enumerate(groups, 1))
    return f'''<!doctype html>
<!-- Generated from demo group info.md files. Edit those files, then run scripts/build_demos.py. -->
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{kind.title()} Demos</title>
  <link rel="stylesheet" href="assets/demos.css">
  <script src="assets/demos.js" defer></script>
</head>
<body>
  <nav aria-label="Page navigation">
    <a href="../README.md">Repository README</a>
    <a href="demos_{other}.html">{other.title()} Demos →</a>
  </nav>
  <main>
    <h1>{kind.title()} Demos</h1>
    <p class="intro">Swipe or use the arrow buttons to browse each group's videos.</p>
    <div class="demo-list">
{articles or '    <p>No demo groups yet.</p>'}
    </div>
  </main>
</body>
</html>
'''


def write_changed(path, text):
    if path.exists() and path.read_text(encoding='utf-8') == text:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + '.tmp')
    pending.write_text(text, encoding='utf-8')
    pending.replace(path)


def build(root):
    output_dir = root / 'documents'
    pages = {}
    for kind in KINDS:
        folder = root / f'demos_{kind}'
        groups = []
        for group in sorted(folder.iterdir()) if folder.exists() else []:
            if group.is_dir():
                create_info(group)
                if (group / 'info.md').exists():
                    groups.append(read_info(group / 'info.md'))
        pages[output_dir / f'demos_{kind}.html'] = render_page(kind, groups, output_dir)
        print(f'{kind.title()}: {len(groups)} groups, {sum(len(g["videos"]) for g in groups)} videos', flush=True)
    # Validate every group before replacing either gallery.
    for path, content in pages.items():
        write_changed(path, content)
    for name in ('demos.css', 'demos.js'):
        source = REPO / 'documents' / 'assets' / name
        write_changed(output_dir / 'assets' / name, source.read_text(encoding='utf-8'))


def snapshot(root):
    paths = []
    for kind in KINDS:
        folder = root / f'demos_{kind}'
        if folder.exists():
            for path in folder.rglob('*'):
                if path.is_dir() or path.name == 'info.md' or path.suffix.lower() in VIDEO_TYPES:
                    stat = path.stat()
                    paths.append((str(path), stat.st_mtime_ns, stat.st_size))
    return tuple(sorted(paths))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=REPO, help='Repository root (default: this script\'s repository)')
    parser.add_argument('--watch', action='store_true', help='Rebuild when metadata or video files change; refresh the browser to view updates')
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        build(root)
    except (OSError, ValueError) as error:
        print(f'Build failed: {error}', file=sys.stderr)
        if not args.watch:
            return 1
    if not args.watch:
        return 0
    previous = snapshot(root)
    print('Watching demo folders. Save info.md to rebuild; refresh your browser. Press Ctrl+C to stop.', flush=True)
    try:
        while True:
            time.sleep(0.5)
            current = snapshot(root)
            if current != previous:
                try:
                    build(root)
                except (OSError, ValueError) as error:
                    print(f'Build failed: {error}', file=sys.stderr)
                previous = snapshot(root)
    except KeyboardInterrupt:
        return 0


if __name__ == '__main__':
    sys.exit(main())
