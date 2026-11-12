# Demo Authoring

Each direct subfolder of `demos_isaac` or `demos_newton` is one demo group. Its videos appear in one horizontal carousel, with shared information on the right. On narrow screens, the information appears below the carousel. Swipe, scroll horizontally, use the arrow buttons, or focus the carousel and press the left/right arrow keys to change videos.

The currently displayed video autoplays muted and loops. Moving to another slide starts that video automatically and pauses the others in the group. Player controls remain available, including sound. Autoplay follows browser settings.

The information area keeps a fixed height. Software Version has one line of content height; Source Repository and Author each have two. Description uses the remaining height. Long text scrolls vertically inside its own content area, keeping the video and group layout stable.

## Edit group information

Every group contains an `info.md` with the same English headings. Fill in text below the headings, outside the HTML comments. Keep the headings and video table column names unchanged. Description supports inline bold text using `**text**`, for example `**MujocoSolver and VBD**`. Other text fields use plain text, and Source Repository accepts a complete HTTP or HTTPS URL. Empty text fields remain blank on the page.

For example:

```markdown
# Demo Information

## Name
Robot Manipulation

## Description
A robot picks up and places objects.

## Software Version
Simulator 1.0

## Source Repository
https://example.com/source

## Author
Author Name

## Author Homepage
https://example.com

## Author Email
author@example.com

## Videos
| Name | Path |
| --- | --- |
| Front view | 01.mp4 |
| Side view | 02.mp4 |
```

`Name` is the displayed group title. Each video row supplies its displayed name and a file path relative to that group's `info.md`. Rows determine slide order. Paths can contain spaces and must point to files inside the group folder. Supported extensions are `.mp4`, `.webm`, `.mov`, and `.m4v`; actual playback depends on the browser and video codec. Use plain cell text without `|` characters.

`Author Homepage` and `Author Email` are optional contact fields. The displayed author name links to the homepage when supplied, or to a `mailto:` link when only an email is supplied. A homepage without a scheme uses HTTPS. If both contact fields are blank, the name stays plain text. These fields do not add rows to the page: the layout still has Description, Software Version, Source Repository, and Author. Older metadata files without the contact headings are also supported.

For multiple authors, use a table under `Author` instead of a single name:

```markdown
## Author
| Name | Homepage | Email |
| --- | --- | --- |
| First Author | https://example.com | |
| Second Author | | author@example.com |
```

Each name gets its own link. Leave unused contact cells blank. In this format, the table supplies each author's contact information; the separate `Author Homepage` and `Author Email` sections can stay blank. The names appear together in the existing Author row, in table order.

## Synchronize the HTML pages

Run from the repository root:

```sh
python3 scripts/build_demos.py
```

The script reads every group's `info.md` and regenerates `documents/demos_isaac.html` and `documents/demos_newton.html`. It preserves existing `info.md` files. If a required heading or video path is invalid, it reports the affected file and leaves the existing HTML pages unchanged.

For automatic rebuilding while editing:

```sh
python3 scripts/build_demos.py --watch
```

Keep the command running, save your edits, and refresh the browser. Stop it with Ctrl+C. Watching updates the HTML files on disk; it does not reload an open browser tab. No background service is installed.

Both generated pages work when opened directly in a browser. Keep `documents/assets` and the demo video directories in their relative locations. If publishing the site, publish the rebuilt HTML, assets, and videos together.

## Add videos or groups

For an existing group, copy the video into its folder and add its Name / Path row to `info.md`. Remove rows when removing videos, and update paths when renaming files. The explicit table controls which videos are displayed.

For a new group, create a subfolder under `demos_isaac` or `demos_newton`, add videos, and run the build command. A new English `info.md` is initialized from the files in that folder, then included in the gallery. Fill in the new template and rebuild. Existing metadata is never overwritten. Group order follows folder names.

## Verification

```sh
python3 -m unittest discover -s tests -v
node --check documents/assets/demos.js
```

Python tests cover initialization, metadata and video-order synchronization, invalid paths, and automatic rebuilding. Node is needed only for the optional JavaScript syntax check.
