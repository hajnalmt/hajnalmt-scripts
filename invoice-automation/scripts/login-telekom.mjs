import { chromium } from 'playwright';

const profileDir = 'browser-profiles/telekom';
const url = 'https://www.telekom.hu/fiokom';

const context = await chromium.launchPersistentContext(profileDir, {
  headless: false,
  acceptDownloads: true,
});
const page = context.pages()[0] || await context.newPage();
await page.goto(url, { waitUntil: 'domcontentloaded' });
console.log('Telekom login window opened. Complete login/2FA manually, then press Enter here to close and save the session.');
process.stdin.resume();
process.stdin.once('data', async () => {
  await context.close();
  process.exit(0);
});
