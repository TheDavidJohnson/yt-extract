# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2026-02-20

### Changed
- Send the YouTube Data API key using the `X-Goog-Api-Key` HTTP header instead of the `key` query parameter.

### Fixed
- Synchronize version metadata to `0.1.2` in both `pyproject.toml` and `yt_extract/__init__.py`.

### Removed
- Remove unused `requests` dependency from `pyproject.toml`.

## [0.1.1] - 2026-02-20

### Changed
- Switch default table output from ASCII grid to Markdown.

### Added
- Add `--format` option to choose between Markdown and ASCII grid output.

## [0.1.0] - 2026-02-20

### Added
- Initial release of `yt-extract`.
- CLI to fetch YouTube video metadata via the YouTube Data API v3.
- Support for API key configuration via `YOUTUBE_DATA_API_KEY`.
- Tabular terminal output for core metadata fields (ID, title, publication date, channel, counts, duration).
