# yt-extract

Fetch YouTube video metadata via the [YouTube Data API v3](https://developers.google.com/youtube/v3/docs) and print a table.

## Requirements

- Python 3.9+
- A Google Cloud project with the YouTube Data API v3 enabled and an API key restricted to that API.

## Installation

From the package directory (or from a parent repo that has this as `tools/yt-extract`):

```bash
pip install -e .
```

Example from a parent repo's root:

```bash
pip install -e tools/yt-extract
```

With a venv active, the `yt-extract` command will be on your PATH.

## Usage

Set your API key, then pass one or more video IDs:

```bash
export YOUTUBE_DATA_API_KEY=your_key
yt-extract dQw4w9WgXcQ
yt-extract VIDEO_ID_1 VIDEO_ID_2
```

If you don’t pass any IDs, you’ll be prompted to enter them (comma- or space-separated):

```bash
yt-extract
# Enter video ID(s), comma- or space-separated: dQw4w9WgXcQ
```

## Output

The default table includes: id, title, publication date, channel title, view count, like count, comment count, duration.

Videos that are private, deleted, or not found are reported on stderr; the table includes only successfully fetched videos.

## API key

- Read from the `YOUTUBE_DATA_API_KEY` environment variable.
- If unset, the tool exits with instructions to set it.
- Do not commit your API key.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for the full text.
