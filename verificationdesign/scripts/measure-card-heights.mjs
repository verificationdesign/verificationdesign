import { mkdir, readFile, readdir } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import puppeteer from 'puppeteer';
import { extractGloss } from '../src/content/loaders/cardsLoader.mjs';

const args = process.argv.slice(2);
const shotsIndex = args.indexOf('--shots');
const shotsDir = shotsIndex >= 0 ? args[shotsIndex + 1] : undefined;
if (shotsIndex >= 0 && !shotsDir) throw new Error('--shots requires a directory');
const positional = args.filter((_, index) => shotsIndex < 0 || (index !== shotsIndex && index !== shotsIndex + 1));
const base = (process.env.SITE_URL || positional[0] || 'http://127.0.0.1:4321').replace(/\/$/, '');
const cardsDir = resolve(process.cwd(), '../ai-design-patterns/cards');
const widths = [1280, 1024, 768, 390, 320];
const rowExpectations = {
  1280: { min: 2, max: 2 },
  768: { min: 3, max: 3 },
  390: { min: 2, max: 2 },
  320: { min: 1, max: 1 },
};
const chooserColumns = { 1280: 3, 1024: 2, 768: 2, 390: 1, 320: 1 };
const headerPositions = { 1280: 'sticky', 768: 'sticky', 390: 'static', 320: 'static' };
const pages = [{ path: '/', name: 'home' }, { path: '/patterns/', name: 'patterns' }];
const failures = [];

function groupRows(items) {
  const rows = new Map();
  for (const item of items) {
    const top = Math.round(item.top);
    if (!rows.has(top)) rows.set(top, []);
    rows.get(top).push(item);
  }
  return [...rows.entries()].sort(([a], [b]) => a - b).map(([, row]) => row);
}

const expected = [];
for (const file of (await readdir(cardsDir)).filter((name) => name.endsWith('.md')).sort()) {
  const gloss = extractGloss(await readFile(join(cardsDir, file), 'utf8'));
  if (!gloss) throw new Error(`Missing source gloss in ${file}`);
  expected.push({ file, gloss });
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
        await page.evaluate(() => document.fonts.ready.then(() => undefined));
        const { scrollWidth, viewportWidth, categories, chooserCards, headerPosition } = await page.evaluate(() => ({
          scrollWidth: document.documentElement.scrollWidth,
          viewportWidth: window.innerWidth,
          headerPosition: getComputedStyle(document.querySelector('.site-header')).position,
          chooserCards: [...document.querySelectorAll('.chooser-card')].map((card) => {
            const { left, top, width } = card.getBoundingClientRect();
            return { left, top, width };
          }),
          categories: [...document.querySelectorAll('.category')].map((category) => ({
            title: category.querySelector('.category-title').textContent.trim(),
            left: category.getBoundingClientRect().left,
            top: category.getBoundingClientRect().top,
            sectionWidth: category.getBoundingClientRect().width,
            listWidth: category.querySelector('.card-list').getBoundingClientRect().width,
            tiles: [...category.querySelectorAll('.card-list li > a')].map((tile) => {
              const rect = tile.getBoundingClientRect();
              const gloss = tile.querySelector('.card-gloss');
              const glossRect = gloss?.getBoundingClientRect();
              const lineHeight = gloss ? parseFloat(getComputedStyle(gloss).lineHeight) : 0;
              const style = getComputedStyle(tile);
              const padding = [style.paddingTop, style.paddingRight, style.paddingBottom, style.paddingLeft];
              return {
                title: tile.querySelector('.card-title').textContent.trim(),
                gloss: gloss?.textContent.trim() ?? '',
                width: rect.width,
                height: rect.height,
                top: rect.top,
                bottom: rect.bottom,
                overflowX: tile.scrollWidth - tile.clientWidth,
                overflowY: tile.scrollHeight - tile.clientHeight,
                lines: glossRect ? Math.round(glossRect.height / lineHeight) : 0,
                lineHeight,
                padding: padding.every((side) => side === padding[0]) ? padding[0] : padding.join('/'),
                glossWidth: glossRect?.width ?? null,
                unused: glossRect
                  ? rect.bottom - parseFloat(style.borderBottomWidth)
                    - parseFloat(style.paddingBottom) - glossRect.bottom
                  : null,
              };
            }),
          })),
        }));
        const context = `${item.path} width=${width}`;
        console.log(`${context} scrollWidth=${scrollWidth}px viewportWidth=${viewportWidth}px`);
        if (scrollWidth > viewportWidth + 1) {
          failures.push(`${context}: document scrollWidth ${scrollWidth}px exceeds viewport width ${viewportWidth}px`);
        }
        const categoryLefts = categories.map(({ left }) => left);
        const categoryTops = categories.map(({ top }) => top);
        const firstTileTops = categories.map(({ tiles }) => tiles[0]?.top);
        console.log(`  category_lefts=[${categoryLefts}] category_tops=[${categoryTops}] first_tile_tops=[${firstTileTops}]`);
        const aligned = (positions) => positions.every(Number.isFinite)
          && Math.max(...positions) - Math.min(...positions) <= 1;
        const chooserRows = groupRows(chooserCards);
        const chooserRowSizes = chooserRows.map((row) => row.length);
        const columns = chooserColumns[width];
        console.log(`  chooser_cards_per_row=[${chooserRowSizes}] header_position=${headerPosition}`);
        if (chooserRows.length !== 6 / columns || chooserRowSizes.some((count) => count !== columns)) {
          failures.push(`${context}: expected six chooser cards with ${columns} per row`);
        }
        if (headerPositions[width] && headerPosition !== headerPositions[width]) {
          failures.push(`${context}: expected header position ${headerPositions[width]}, got ${headerPosition}`);
        }
        if (width === 1280) {
          if (categories.length !== 3 || new Set(categoryLefts).size !== 3 || !aligned(categoryTops)) {
            failures.push(`${context}: expected three side-by-side categories with aligned tops`);
          }
          if (!aligned(firstTileTops)) failures.push(`${context}: first tiles are vertically misaligned`);
          for (const [rowIndex, row] of chooserRows.entries()) {
            for (const [columnIndex, card] of row.sort((a, b) => a.left - b.left).entries()) {
              const category = categories[columnIndex];
              const column = `chooser row ${rowIndex + 1} column ${columnIndex + 1}`;
              console.log(`  ${column} left=${card.left.toFixed(2)}px width=${card.width.toFixed(2)}px category_left=${category?.left.toFixed(2) ?? 'n/a'}px category_width=${category?.sectionWidth.toFixed(2) ?? 'n/a'}px`);
              if (!category || Math.abs(card.left - category.left) > 1
                  || Math.abs(card.width - category.sectionWidth) > 1) {
                failures.push(`${context}: ${column} differs from the category column by more than 1px or has no match`);
              }
            }
          }
        } else {
          if (categories.length !== 3 || !aligned(categoryLefts) || new Set(categoryTops).size !== 3) {
            failures.push(`${context}: expected three categories with one per row`);
          }
        }
        const tiles = categories.flatMap(({ tiles }) => tiles);
        const glossCounts = expected.map(({ file, gloss }) => ({
          file, count: tiles.filter((tile) => tile.gloss === gloss).length,
        }));
        const once = glossCounts.filter(({ count }) => count === 1).length;
        const lines = tiles.map((tile) => tile.lines);
        const spread = (key) => tiles.length
          ? Math.max(...tiles.map((tile) => tile[key])) - Math.min(...tiles.map((tile) => tile[key]))
          : null;
        console.log(`${context} tiles=${tiles.length} glosses_once=${once}/${expected.length} width_spread=${spread('width')} height_spread=${spread('height')}`);
        console.log(`  gloss_lines min=${lines.length ? Math.min(...lines) : 'n/a'} max=${lines.length ? Math.max(...lines) : 'n/a'} list=[${lines}]`);

        const allRowGaps = [];
        for (const { title, sectionWidth, listWidth, tiles: group } of categories) {
          const rows = groupRows(group);
          const rowSizes = rows.map((row) => row.length);
          const rowGaps = rows.slice(1).map((row, index) =>
            Math.min(...row.map((tile) => tile.top)) - Math.max(...rows[index].map((tile) => tile.bottom)));
          allRowGaps.push(...rowGaps);
          console.log(`  ${title} tiles_per_row=[${rowSizes}] row_gaps=[${rowGaps.map((gap) => gap.toFixed(2))}]px card_list_width=${listWidth.toFixed(2)}px category_width=${sectionWidth.toFixed(2)}px`);
          if (!aligned(rowGaps)) failures.push(`${context} ${title}: tile row gaps differ by more than 1px`);
          const expectation = rowExpectations[width];
          if (expectation) {
            const { min, max } = expectation;
            const fullRows = rowSizes.slice(0, -1);
            const lastRow = rowSizes.at(-1);
            if (fullRows.some((count) => count < min || count > max)
                || lastRow > (fullRows[0] ?? max)) {
              failures.push(`${context} ${title}: row sizes [${rowSizes}] violate expected full row size ${min}-${max} with a potentially shorter last row`);
            }
          }
          for (const tile of group) {
            console.log(`    ${tile.title}: ${tile.width.toFixed(2)}x${tile.height.toFixed(2)}px overflow=${tile.overflowX}x${tile.overflowY}px unused_bottom=${tile.unused?.toFixed(2) ?? 'n/a'}px gloss_line_height=${tile.lineHeight}px padding=${tile.padding} gloss_width=${tile.glossWidth === null ? 'n/a' : `${tile.glossWidth.toFixed(2)}px`}`);
          }
        }
        if (!aligned(allRowGaps)) failures.push(`${context}: tile row gaps across categories differ by more than 1px`);

        if (shotsDir) await page.screenshot({ path: join(shotsDir, `${item.name}-${width}.png`), fullPage: true });
        if (width === 1280) {
          const { headerTop, scrollY } = await page.evaluate(async () => {
            window.scrollTo(0, document.documentElement.scrollHeight);
            await new Promise((resolve) => requestAnimationFrame(resolve));
            return { headerTop: document.querySelector('.site-header').getBoundingClientRect().top, scrollY: window.scrollY };
          });
          console.log(`  bottom_scroll_y=${scrollY}px header_top=${headerTop.toFixed(2)}px`);
          if (scrollY <= 0 || Math.abs(headerTop) > 1) {
            failures.push(`${context}: expected scrolled page with header top within 1px of 0`);
          }
        }
        if (tiles.length !== expected.length) failures.push(`${context}: unexpected tile count ${tiles.length}`);
        for (const { file, count } of glossCounts) {
          if (count !== 1) failures.push(`${context}: ${file} gloss occurs ${count} times`);
        }
        if (width !== 320 && (spread('width') > 1 || spread('height') > 1)) {
          failures.push(`${context}: tile sizes differ by more than 1px`);
        }
        for (const tile of tiles) {
          const label = `${context} ${tile.title}`;
          if (width !== 320 && Math.abs(tile.width - tile.height) > 2) failures.push(`${label}: tile is not square`);
          if (tile.overflowX > 1 || tile.overflowY > 1) failures.push(`${label}: content overflows tile`);
          if (width !== 320 && tile.unused > 2 * tile.lineHeight) {
            failures.push(`${label}: more than two gloss lines of unused height`);
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
console.log(`Summary: ${pages.length * widths.length} viewport checks, ${failures.length} failures`);
if (failures.length) process.exit(1);
