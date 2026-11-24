import { readFile, readdir } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, resolve, sep } from 'node:path';
import puppeteer from 'puppeteer';

const dist = resolve('dist');
const widths = [320, 339, 340, 390, 768, 1024, 1280];
const schemes = ['light', 'dark'];
const types = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.woff2': 'font/woff2',
};

const pages = (await readdir(dist, { recursive: true, withFileTypes: true }))
  .filter((entry) => entry.isFile() && entry.name.endsWith('.html'))
  .map((entry) => join(entry.parentPath ?? entry.path, entry.name).slice(dist.length + 1))
  .sort()
  .map((file) => {
    const path = '/' + file.split(sep).map(encodeURIComponent).join('/');
    return path.replace(/\/index\.html$/, '/');
  });
if (!pages.length) throw new Error('No HTML pages found in dist. Run npm run build first.');
for (const required of ['/', '/patterns/']) {
  if (!pages.includes(required)) throw new Error(`Required page ${required} not found in dist.`);
}

function hasOrphanTileRow(tileTops) {
  const rowSizes = new Map();
  for (const top of tileTops) {
    const row = Math.round(top);
    rowSizes.set(row, (rowSizes.get(row) ?? 0) + 1);
  }
  const lastRow = Math.max(...rowSizes.keys());
  return rowSizes.get(lastRow) === 1 && [...rowSizes.values()].some((size) => size > 1);
}

function isShortNavTarget(height) {
  return height < 44;
}

const server = createServer(async (request, response) => {
  try {
    const path = decodeURIComponent(new URL(request.url, 'http://127.0.0.1').pathname);
    const file = resolve(dist, '.' + (path.endsWith('/') ? path + 'index.html' : path));
    if (!file.startsWith(dist + sep)) {
      response.writeHead(403).end();
      return;
    }
    const body = await readFile(file);
    response.writeHead(200, { 'Content-Type': types[extname(file)] ?? 'application/octet-stream' }).end(body);
  } catch (error) {
    const status = error.code === 'ENOENT' || error.code === 'EISDIR' ? 404 : 500;
    response.writeHead(status).end();
  }
});

await new Promise((resolve, reject) => {
  server.once('error', reject);
  server.listen(0, '127.0.0.1', resolve);
});

let browser;
let failures = 0;
let configurations = 0;
const base = `http://127.0.0.1:${server.address().port}`;

try {
  browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  for (const width of widths) {
    await page.setViewport({ width, height: 900, deviceScaleFactor: 1 });
    for (const scheme of schemes) {
      await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: scheme }]);
      for (const path of pages) {
        if ([339, 340, 768, 1024].includes(width) && path !== '/' && path !== '/patterns/') continue;
        configurations += 1;
        const checkTileRows = path === '/patterns/' && width >= 768;
        const checkNavTargets = width < 720;
        const configuration = `${path} width=${width} scheme=${scheme}`;
        try {
          const response = await page.goto(base + path, { waitUntil: 'networkidle0' });
          if (!response?.ok()) throw new Error(`HTTP ${response?.status() ?? 'no response'}`);
          const { scrollWidth, wideElements, families, navTargets, navTops } = await page.evaluate(async ({
            viewportWidth, checkTileRows, checkNavTargets,
          }) => {
            await document.fonts.ready;
            // Closed details hide content that can overflow once opened (the home catalog).
            for (const details of document.querySelectorAll('details')) details.open = true;
            const scrollWidth = document.documentElement.scrollWidth;
            const wideElements = scrollWidth > viewportWidth
              ? [...document.querySelectorAll('*')].flatMap((element) => {
                  const width = element.getBoundingClientRect().width;
                  return width > viewportWidth
                    ? [{ tag: element.localName, className: element.getAttribute('class') ?? '', width }]
                    : [];
                })
              : [];
            const families = checkTileRows ? [...document.querySelectorAll('.category')].map((family) => ({
              name: family.id,
              tileTops: [...family.querySelectorAll('.card-list li > a')].map(
                (tile) => tile.getBoundingClientRect().top,
              ),
              unmeasurable: [...family.querySelectorAll('.card-list li > a')].filter((tile) => {
                const { width, height } = tile.getBoundingClientRect();
                return !(width > 0 && height > 0);
              }).length,
            })) : [];
            const navTargets = checkNavTargets ? [...document.querySelectorAll('.site-header nav a')].map((link) => ({
              text: link.textContent.trim(),
              height: link.getBoundingClientRect().height,
            })) : [];
            // Every nav item, including the current-page span, for the one-row check.
            const navTops = checkNavTargets ? [...document.querySelectorAll('.site-header nav li > *')].map(
              (item) => item.getBoundingClientRect().top,
            ) : [];
            return { scrollWidth, wideElements, families, navTargets, navTops };
          }, { viewportWidth: width, checkTileRows, checkNavTargets });
          console.log(`${configuration} scrollWidth=${scrollWidth}`);
          if (scrollWidth > width) {
            failures += 1;
            console.error(`FAIL: ${configuration} overflows by ${scrollWidth - width}px`);
            for (const { tag, className, width: elementWidth } of wideElements) {
              console.error(`  tag=${tag} class=${JSON.stringify(className)} width=${elementWidth}`);
            }
          }
          if (checkTileRows && families.length === 0) {
            failures += 1;
            console.error(`FAIL: ${configuration} no pattern family found for the tile row check`);
          }
          if (checkNavTargets && navTargets.length === 0) {
            failures += 1;
            console.error(`FAIL: ${configuration} no header nav link found for the tap target check`);
          }
          for (const { name, tileTops, unmeasurable } of families) {
            if (tileTops.length < 2 || unmeasurable > 0 || new Set(tileTops.map(Math.round)).size < 2) {
              failures += 1;
              console.error(`FAIL: ${configuration} ${name} tile rows not measurable (tiles=${tileTops.length} unmeasurable=${unmeasurable})`);
              continue;
            }
            if (hasOrphanTileRow(tileTops)) {
              failures += 1;
              console.error(`FAIL: ${configuration} ${name} has a single tile in its last row`);
            }
          }
          if (checkNavTargets && (navTops.length !== 4 || Math.max(...navTops) - Math.min(...navTops) > 1)) {
            failures += 1;
            console.error(`FAIL: ${configuration} expected four header nav items on one row, got tops [${navTops.map((top) => top.toFixed(1))}]`);
          }
          for (const { text, height } of navTargets) {
            if (isShortNavTarget(height)) {
              failures += 1;
              console.error(`FAIL: ${configuration} nav target "${text}" is ${height}px tall, expected at least 44px`);
            }
          }
        } catch (error) {
          failures += 1;
          console.error(`FAIL: ${configuration} measurement_error=${JSON.stringify(error.message)}`);
        }
      }
    }
  }
} finally {
  try {
    await browser?.close();
  } finally {
    await new Promise((resolve, reject) => server.close((error) => error ? reject(error) : resolve()));
  }
}

console.log(`Layout checks: pages=${pages.length} configurations=${configurations} failures=${failures}`);
if (failures) process.exitCode = 1;
