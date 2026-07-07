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

## Google OAuth setup for Gmail/Drive API access

This is the preferred path for ChatGPT Plus receipts because it avoids saving a
Google password or relying on browser sessions.

1. Create a Google Cloud project.
2. Enable these APIs:
   - Gmail API
   - Google Drive API
3. Configure the OAuth consent screen. For a personal script, keep it in testing
   and add your own Google account as a test user.
4. Create an OAuth client:
   - Application type: Desktop app
   - Authorized redirect URI used by the script: `http://127.0.0.1:53682/oauth2callback`
5. Create local `.env` from `.env.example` style values:

```bash
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
GOOGLE_OAUTH_PORT=53682
GOOGLE_OAUTH_TOKEN_PATH=secrets/google-token.json
GMAIL_OPENAI_QUERY='from:(openai.com OR stripe.com) (ChatGPT OR OpenAI OR invoice OR receipt)'
```

6. Run OAuth on a machine where you can open the browser locally:

```bash
npm run google:oauth
```

The token is saved to `secrets/google-token.json`, which is gitignored. If you
run the OAuth flow on your laptop, copy only that token file into the same path
on Hermes.

7. Probe Gmail without downloading anything:

```bash
npm run gmail:probe
```
