import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();
await page.goto('data:text/html,<title>invoice automation smoke</title><h1>ok</h1>');
const title = await page.title();
await browser.close();
if (title !== 'invoice automation smoke') {
  throw new Error(`unexpected title: ${title}`);
}
console.log('Playwright Chromium smoke test passed');
