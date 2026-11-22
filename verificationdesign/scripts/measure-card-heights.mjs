import { mkdir, readFile, readdir } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import puppeteer from 'puppeteer';

const args = process.argv.slice(2);
const shotsIndex = args.indexOf('--shots');
const shotsDir = shotsIndex >= 0 ? args[shotsIndex + 1] : undefined;
if (shotsIndex >= 0 && !shotsDir) throw new Error('--shots requires a directory');
const positional = args.filter((_, index) => shotsIndex < 0 || (index !== shotsIndex && index !== shotsIndex + 1));
const base = (process.env.SITE_URL || positional[0] || 'http://127.0.0.1:4321').replace(/\/$/, '');
const cardsDir = resolve(process.cwd(), '../ai-design-patterns/cards');
const widths = [1280, 390];
const pages = [{ path: '/', name: 'home' }, { path: '/patterns/', name: 'patterns' }];
const failures = [];

function sourceBody(text) {
  return `${text.replace(/\r\n/g, '\n').replace(/\n*$/, '')}\n`;
}

function intentOf(text) {
  return text.match(/^## Intent\s*\n+([^\n]+)/m)?.[1]?.replace(/[*`]/g, '').trim().replace(/\s+/g, ' ') ?? '';
}

function decodeHtml(value) {
  return value.replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)))
    .replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'").replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
}

const intents = [];
for (const file of (await readdir(cardsDir)).filter((name) => name.endsWith('.md'))) {
  const intent = intentOf(sourceBody(await readFile(join(cardsDir, file), 'utf8')));
  if (intent) intents.push(intent);
}

if (shotsDir) await mkdir(shotsDir, { recursive: true });
const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });

try {
  for (const item of pages) {
    for (const width of widths) {
      const page = await browser.newPage();
      await page.setViewport({ width, height: 900, deviceScaleFactor: 1 });
      try {
        await page.goto(`${base}${item.path}`, { waitUntil: 'networkidle0' });
        const measurement = await page.evaluate(() => ({
          categories: [...document.querySelectorAll('.category')].map((category) => ({
            title: category.querySelector('.category-title')?.textContent?.trim() ?? '',
            heights: [...category.querySelectorAll('.card-list li > a')].map((card) => Math.round(card.getBoundingClientRect().height)),
          })),
          lineHeight: Number.parseFloat(getComputedStyle(document.querySelector('.card-gloss')).lineHeight) || 24,
        }));
        const html = decodeHtml(await page.content());
        const intentCounts = intents.map((intent) => html.split(intent).length - 1);
        const intentsOnce = intentCounts.filter((count) => count === 1).length;
        const heights = measurement.categories.map(({ title, heights: values }) => `${JSON.stringify(title)}=[${values.join(',')}]`).join(' ');
        console.log(`${item.path} width=${width} heights=${heights} intents_once=${intentsOnce}/${intents.length}`);

        if (shotsDir) await page.screenshot({ path: join(shotsDir, `${item.name}-${width}.png`), fullPage: true });
        if (intentsOnce !== intents.length) failures.push(`${item.path} width=${width}: intents_once=${intentsOnce}/${intents.length}`);
        for (const category of measurement.categories) {
          if (new Set(category.heights).size > 1) failures.push(`${item.path} width=${width}: unequal heights in ${category.title}`);
        }
        if (width === 1280) {
          const categoryHeights = measurement.categories.map((category) => Math.max(...category.heights));
          if (Math.max(...categoryHeights) - Math.min(...categoryHeights) > measurement.lineHeight) {
            failures.push(`${item.path} width=${width}: category height spread exceeds line height ${measurement.lineHeight}px`);
          }
        }
      } catch (error) {
        console.log(`${item.path} width=${width} measurement_error=${JSON.stringify(error.message)}`);
        failures.push(`${item.path} width=${width}: ${error.message}`);
      } finally {
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
}

for (const failure of failures) console.error(`FAIL: ${failure}`);
if (failures.length) process.exit(1);
