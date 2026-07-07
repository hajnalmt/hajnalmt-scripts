import 'dotenv/config';
import http from 'node:http';
import fs from 'node:fs/promises';
import { google } from 'googleapis';

const clientId = process.env.GOOGLE_OAUTH_CLIENT_ID;
const clientSecret = process.env.GOOGLE_OAUTH_CLIENT_SECRET;
const port = Number(process.env.GOOGLE_OAUTH_PORT || 53682);
const tokenPath = process.env.GOOGLE_OAUTH_TOKEN_PATH || 'secrets/google-token.json';

if (!clientId || !clientSecret) {
  console.error('Missing GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET in .env');
  process.exit(1);
}

const redirectUri = `http://127.0.0.1:${port}/oauth2callback`;
const oauth2Client = new google.auth.OAuth2(clientId, clientSecret, redirectUri);
const scopes = [
  'https://www.googleapis.com/auth/gmail.readonly',
  'https://www.googleapis.com/auth/drive.file',
];

const authUrl = oauth2Client.generateAuthUrl({
  access_type: 'offline',
  prompt: 'consent',
  scope: scopes,
});

console.log('\nOpen this URL in a browser on the same machine running this script:\n');
console.log(authUrl);
console.log(`\nWaiting for callback on ${redirectUri} ...\n`);

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url || '/', redirectUri);
    if (url.pathname !== '/oauth2callback') {
      res.writeHead(404);
      res.end('Not found');
      return;
    }

    const code = url.searchParams.get('code');
    const error = url.searchParams.get('error');
    if (error) throw new Error(`OAuth error: ${error}`);
    if (!code) throw new Error('OAuth callback missing code');

    const { tokens } = await oauth2Client.getToken(code);
    await fs.mkdir(tokenPath.split('/').slice(0, -1).join('/') || '.', { recursive: true });
    await fs.writeFile(tokenPath, JSON.stringify(tokens, null, 2), { mode: 0o600 });

    res.writeHead(200, { 'content-type': 'text/plain; charset=utf-8' });
    res.end(`Google OAuth token saved to ${tokenPath}. You can close this tab.\n`);

    console.log(`Saved token to ${tokenPath}`);
    server.close(() => process.exit(0));
  } catch (err) {
    res.writeHead(500, { 'content-type': 'text/plain; charset=utf-8' });
    res.end(`${err.message}\n`);
    console.error(err);
  }
});

server.listen(port, '127.0.0.1');
