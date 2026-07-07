import { chromium } from 'playwright';

const profileDir = 'browser-profiles/openai';
const url = 'https://platform.openai.com/settings/organization/billing/history';

const context = await chromium.launchPersistentContext(profileDir, {
  headless: false,
  acceptDownloads: true,
});
const page = context.pages()[0] || await context.newPage();
await page.goto(url, { waitUntil: 'domcontentloaded' });
console.log('OpenAI login window opened. Complete login/2FA manually, then press Enter here to close and save the session.');
process.stdin.resume();
process.stdin.once('data', async () => {
  await context.close();
  process.exit(0);
});
