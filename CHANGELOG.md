# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),  
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.0.1] - 2025-09-30
### Added
- First stable release of Paperless → Nextcloud export utility
- Rule-based routing via `routing.json`
  - `tags_any` / `tags_all`
  - `correspondent` (by ID or name)
  - `document type` (by ID or name)
  - `title_contains`
- Filename templating (`{created}`, `{title}`, `{correspondent}`, `{type}`)
- Environment-based configuration via `.env`
- Upload options (`overwrite`, `original`)
- Portable scripts:
  - `export.sh` (generic)
  - `examples/export.unraid.sh` (Unraid User Scripts plugin)
- Example configs:
  - `.env.example`
  - `examples/routing.json.example`

---

[1.0.0]: https://github.com/cheynolds/paperless-nextcloud-export/releases/tag/v1.0.0
