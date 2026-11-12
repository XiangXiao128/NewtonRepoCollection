# NewtonRepoCollection

Demo pages:

- [Isaac Demos](documents/demos_isaac.html): 3 groups, 9 videos.
- [Newton Demos](documents/demos_newton.html): 5 groups, 12 videos.

After downloading the repository, open an HTML page in `documents` with a browser to watch the videos. GitHub's repository view displays HTML source; the static pages can be published with GitHub Pages for online playback.

Each subfolder is one demo group. Swipe horizontally or use Previous / Next to browse its videos. The group shares four information rows: Description, Software Version, Source Repository, and Author.

The current video starts automatically, muted and looping. Switching slides starts the newly displayed video and pauses the other videos in that group. Use the player controls to enable sound if needed.

Edit the English `info.md` in a demo subfolder to update its name, shared information, video names, relative paths, and slide order. From the repository root, synchronize both HTML pages with Python 3.9 or newer (no extra packages required):

```sh
python3 scripts/build_demos.py
```

For automatic synchronization while editing, run the following command from the repository root and keep the terminal running:

```sh
python3 scripts/build_demos.py --watch
```

Edit and save any demo subfolder's `info.md` (for example, `demos_newton/demo03/info.md`). The watcher automatically regenerates both HTML pages. Refresh the corresponding page in your browser to see the latest text; the browser tab does not reload automatically.

Press Ctrl+C to stop watching. Without the watcher running, saved Markdown changes do not update the HTML automatically; run `python3 scripts/build_demos.py` once to synchronize them instead.

See [Demo Authoring](documents/demo-authoring.md) for the template and instructions for adding videos or groups. Generated HTML should not be edited directly.
