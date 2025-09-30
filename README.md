# Paperless → Nextcloud Export

This project provides scripts to export documents from Paperless-ngx into Nextcloud using WebDAV.  
It supports routing rules (by tags, correspondents, document type, etc.) and works in both generic Linux setups and Unraid environments.

---

## Features

- Export Paperless documents as PDFs into Nextcloud.
- Routing rules via `routing.json`:
  - Match by tags (`tags_any`, `tags_all`).
  - Match by correspondent (ID or name).
  - Match by document type.
  - Match by title substring.
- Filename templating (e.g. `{created} - {title}.pdf`).
- Supports overwrite or append mode.
- Portable: works in any Docker environment, with an extra script for Unraid User Scripts.
- Handles Tika and Gotenberg backends required by Paperless.

---

## Requirements

- Paperless-ngx (with API access enabled).
- Tika and Gotenberg containers running (Paperless depends on them for parsing).
- Nextcloud with WebDAV enabled (`remote.php/dav/files/<username>/`).
- Docker (if you want to run inside container context).

---

## Setup

1. Clone this repo:
   git clone https://github.com/cheynolds/paperless-nextcloud-export.git
   cd paperless-nextcloud-export

2. Copy `.env.example` to `.env` and edit with your values.

3. Adjust routing rules:
   - Copy `examples/routing.json.example` to `routing.json`.
   - Edit destinations and rules as needed.

---

## Usage

### Generic (any Linux / Docker host)
Run the export manually:
   ./export.sh

Or schedule via cron (e.g. every 10 minutes):
   */10 * * * * /path/to/export.sh

### Unraid
Use the included User Script:
- Copy `examples/export.unraid.sh` into `/boot/config/plugins/user.scripts/scripts/`.
- Adjust `.env` path inside script.
- Schedule it from Unraid’s User Scripts plugin (e.g. every 10 minutes).

---

## Example Routing

`routing.json.example`:

{
  "rules": [
    { "if": { "tags_any": ["Taxes"] }, "to": "FAMILY/Finance/Taxes/{year}/" },
    { "if": { "correspondent": "Amazon" }, "to": "FAMILY/Receipts/Amazon/{year}/" },
    { "default": true, "to": "FAMILY/Unfiled/{year}/" }
  ],
  "filename_template": "{created} - {title}.pdf",
  "upload": { "original": false, "overwrite": true }
}

---

## Troubleshooting

- Already processed mails: Clear Paperless mail logs from the SQLite DB if you want to reimport.
- MKCOL 405 errors: These just mean the Nextcloud folder already exists (safe to ignore).
- 404 errors: Check your BASE_NC_URL — it must include `/remote.php/dav/files/<username>/`.

---

## License

MIT License. See LICENSE.
