// End-to-end smoke test: boots the built game in headless Chromium with
// software WebGL, plays through menu → creator → store → equip → runway →
// results, and saves screenshots at each beat. Fails on any page error.
import puppeteer from 'puppeteer';
import { mkdirSync } from 'fs';

const BASE = process.env.BASE_URL || 'http://localhost:4173/?fast&potato';
mkdirSync('test/shots', { recursive: true });

const browser = await puppeteer.launch({
  args: ['--no-sandbox', '--use-gl=swiftshader', '--enable-unsafe-swiftshader',
    '--window-size=960,600'],
  defaultViewport: { width: 960, height: 600 },
});
const page = await browser.newPage();
// software GL renders ~3-10 fps; scale game time so walks/cinematics finish
await page.evaluateOnNewDocument(() => { window.__FF_TIMESCALE = 3; });

const errors = [];
page.on('pageerror', (e) => { errors.push('PAGEERROR: ' + e.message); console.error('PAGEERROR:', e.message); });
page.on('console', (m) => {
  if (m.type() === 'error') { errors.push('CONSOLE: ' + m.text()); console.error('CONSOLE:', m.text()); }
});

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const shot = (name) => page.screenshot({ path: `test/shots/${name}.png` });

console.log('— loading', BASE);
await page.goto(BASE, { waitUntil: 'domcontentloaded', timeout: 120000 });
await page.waitForSelector('.wordmark', { timeout: 120000 });
console.log('— menu rendered');
await sleep(2500);
await shot('1-menu');

// menu → creator
await page.evaluate(() => {
  [...document.querySelectorAll('button')].find((b) => b.textContent.includes('ENTER THE FIT'))?.click();
});
await sleep(1800);
await shot('2-creator');

// pick another preset + drag a slider to prove rebuilds work
await page.evaluate(() => {
  [...document.querySelectorAll('button')].find((b) => b.textContent.includes('Anime Hero'))?.click();
});
await sleep(800);
await page.evaluate(() => {
  [...document.querySelectorAll('button')].find((b) => b.textContent.includes('Curvy'))?.click();
});
await sleep(1000);
await shot('3-creator-preset');

// creator → store
await page.evaluate(() => {
  [...document.querySelectorAll('button')].find((b) => b.textContent.includes('ENTER THE STORE'))?.click();
});
await sleep(2800);
await shot('4-store');

// walk to the bottoms rack: S toward the south wall, then D to strafe
await page.keyboard.down('KeyS');
await sleep(4200);
await page.keyboard.up('KeyS');
await page.keyboard.down('KeyD');
await sleep(1100);
await page.keyboard.up('KeyD');
await sleep(400);
await shot('5-near-rack');

const prompt = await page.evaluate(() => document.getElementById('hud-prompt')?.textContent);
console.log('— prompt near rack:', JSON.stringify(prompt));

// open browse, equip the first two items
await page.keyboard.press('KeyE');
await sleep(900);
await shot('6-browse');
await page.evaluate(() => {
  const btns = [...document.querySelectorAll('#browse .card button')];
  btns[0]?.click();
});
await sleep(700);
await shot('7-equipped');
await page.keyboard.press('KeyE');
await sleep(500);

// present the fit → runway cinematic (headless software GL runs the game
// clock slower than wall time, so poll for the results screen)
await page.keyboard.press('KeyR');
await sleep(7000);
await shot('8-runway-walk');
await sleep(12000);
await shot('9-runway-spin');
await page.waitForSelector('#results .score-big', { timeout: 120000 });
await sleep(600);
await shot('10-results');

const results = await page.evaluate(() => ({
  score: document.querySelector('#results .score-big')?.textContent,
  rank: document.querySelector('#results .rank')?.textContent,
}));
console.log('— results:', JSON.stringify(results));

await browser.close();

if (errors.length) {
  console.error('\n=== ERRORS ===');
  for (const e of errors) console.error(e);
  process.exit(1);
}
if (!results.score) {
  console.error('FAIL: results screen never appeared');
  process.exit(1);
}
console.log('\nSMOKE TEST PASSED — full loop menu→creator→store→equip→runway→results');
