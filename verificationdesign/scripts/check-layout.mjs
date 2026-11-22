import { readFile, readdir } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, resolve, sep } from 'node:path';
import puppeteer from 'puppeteer';

const dist = resolve('dist');
const widths = [320, 390, 1280];
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
const base = `http://127.0.0.1:${server.address().port}`;

try {
  browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  for (const width of widths) {
    await page.setViewport({ width, height: 900, deviceScaleFactor: 1 });
    for (const scheme of schemes) {
      await page.emulateMediaFeatures([{ name: 'prefers-color-scheme', value: scheme }]);
      for (const path of pages) {
        const configuration = `${path} width=${width} scheme=${scheme}`;
        try {
          const response = await page.goto(base + path, { waitUntil: 'networkidle0' });
          if (!response?.ok()) throw new Error(`HTTP ${response?.status() ?? 'no response'}`);
          const { scrollWidth, wideElements } = await page.evaluate(async (viewportWidth) => {
            await document.fonts.ready;
            const scrollWidth = document.documentElement.scrollWidth;
            const wideElements = scrollWidth > viewportWidth
              ? [...document.querySelectorAll('*')].flatMap((element) => {
                  const width = element.getBoundingClientRect().width;
                  return width > viewportWidth
                    ? [{ tag: element.localName, className: element.getAttribute('class') ?? '', width }]
                    : [];
                })
              : [];
            return { scrollWidth, wideElements };
          }, width);
          console.log(`${configuration} scrollWidth=${scrollWidth}`);
          if (scrollWidth > width) {
            failures += 1;
            console.error(`FAIL: ${configuration} overflows by ${scrollWidth - width}px`);
            for (const { tag, className, width: elementWidth } of wideElements) {
              console.error(`  tag=${tag} class=${JSON.stringify(className)} width=${elementWidth}`);
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

console.log(`Layout checks: pages=${pages.length} configurations=${pages.length * widths.length * schemes.length} failures=${failures}`);
if (failures) process.exitCode = 1;
