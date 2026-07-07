import 'dotenv/config';
import fs from 'node:fs/promises';
import { google } from 'googleapis';

const clientId = process.env.GOOGLE_OAUTH_CLIENT_ID;
const clientSecret = process.env.GOOGLE_OAUTH_CLIENT_SECRET;
const tokenPath = process.env.GOOGLE_OAUTH_TOKEN_PATH || 'secrets/google-token.json';
const query = process.env.GMAIL_OPENAI_QUERY || 'from:(openai.com OR stripe.com) (ChatGPT OR OpenAI OR invoice OR receipt)';

if (!clientId || !clientSecret) {
  console.error('Missing GOOGLE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_SECRET in .env');
  process.exit(1);
}

const redirectUri = `http://127.0.0.1:${process.env.GOOGLE_OAUTH_PORT || 53682}/oauth2callback`;
const oauth2Client = new google.auth.OAuth2(clientId, clientSecret, redirectUri);
const tokens = JSON.parse(await fs.readFile(tokenPath, 'utf8'));
oauth2Client.setCredentials(tokens);

const gmail = google.gmail({ version: 'v1', auth: oauth2Client });
const list = await gmail.users.messages.list({
  userId: 'me',
  q: query,
  maxResults: 10,
});

const messages = list.data.messages || [];
console.log(`Query: ${query}`);
console.log(`Found ${messages.length} recent matching messages.`);

for (const message of messages) {
  const detail = await gmail.users.messages.get({
    userId: 'me',
    id: message.id,
    format: 'metadata',
    metadataHeaders: ['From', 'Subject', 'Date'],
  });
  const headers = Object.fromEntries((detail.data.payload?.headers || []).map((h) => [h.name, h.value]));
  console.log(`- ${headers.Date || 'no date'} | ${headers.From || 'no from'} | ${headers.Subject || 'no subject'}`);
}
