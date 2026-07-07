# Invoice automation

Monthly invoice downloader for OpenAI and Telekom portals, with Google Drive upload via `rclone`.

## Security model

- Do not store portal passwords in this repository.
- Browser login sessions live in `browser-profiles/` and are gitignored.
- Downloaded invoices and state files are gitignored.
- Google Drive auth is handled by `rclone` outside git.

## Planned workflow

1. Manual one-time login refresh for each portal with Playwright persistent profiles.
2. Monthly downloader reuses the saved browser session.
3. Downloads latest invoice PDFs.
4. Renames and deduplicates by checksum/state.
5. Uploads to Google Drive using `rclone`.
6. Sends/returns a concise summary.

## Setup status

Run:

```bash
npm run doctor
```

Then configure Google Drive with rclone and run login setup scripts.
