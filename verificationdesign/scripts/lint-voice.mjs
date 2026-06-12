// Voice continuity lint for site prose pages.
//
// The site's prose pages speak in a collective, declarative register; the
// About page is the one designated first-person corner. This check fails the
// build when first-person singular leaks into any other prose page, so a
// register drift is a red gate, not a reader's surprise.
//
// Scope: rendered prose pages in dist/. Pattern-card pages are excluded;
// card prose is governed by the card linter and the catalog's own editorial
// rules, not this check.
//
// Run after `astro build`: node scripts/lint-voice.mjs

import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

const DIST = new URL('../dist', import.meta.url).pathname;

if (!existsSync(DIST)) {
  console.error('[FAIL] voice lint: dist/ not found; run astro build first');
  process.exit(1);
}

// Pages allowed to use first-person singular.
const ALLOWLIST = new Set(['about/index.html']);

// Card pages live at patterns/<category>/<slug>/; the patterns index itself
// (patterns/index.html) is a prose page and stays in scope.
const CARD_PAGE = /^patterns\/[^/]+\/[^/]+\/index\.html$/;

// Matches lowercase and sentence-start capitalized forms; all-caps tokens
// (acronyms like "ME") stay unmatched by construction.
const FIRST_PERSON = /\b(I|I'm|I've|I'd|I'll|[Mm]e|[Mm]y|[Mm]ine|[Mm]yself)\b/g;

function htmlFiles(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) out.push(...htmlFiles(path));
    else if (name.endsWith('.html')) out.push(path);
  }
  return out;
}

function visibleText(html) {
  return html
    .replace(/<script\b[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style\b[\s\S]*?<\/style>/gi, ' ')
    .replace(/<pre\b[\s\S]*?<\/pre>/gi, ' ')
    .replace(/<code\b[\s\S]*?<\/code>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&[a-z#0-9]+;/gi, "'");
}

let pagesChecked = 0;
let failures = 0;

for (const file of htmlFiles(DIST)) {
  const page = relative(DIST, file);
  if (ALLOWLIST.has(page) || CARD_PAGE.test(page)) continue;
  pagesChecked += 1;

  const text = visibleText(readFileSync(file, 'utf8'));
  const hits = [];
  for (const match of text.matchAll(FIRST_PERSON)) {
    const token = match[0];
    // Roman-numeral "I" after a structural word ("Part I", "Chapter I") is
    // not first person.
    if (token === 'I' && /(?:Part|Chapter|Section|Volume|Appendix)\s+$/.test(text.slice(0, match.index))) {
      continue;
    }
    const start = Math.max(0, match.index - 40);
    hits.push(`"...${text.slice(start, match.index + token.length + 40).replace(/\s+/g, ' ').trim()}..."`);
  }

  if (hits.length > 0) {
    failures += 1;
    console.error(`[FAIL] first-person singular in ${page}: ${hits.length} hit(s)`);
    for (const h of hits) console.error(`       ${h}`);
  }
}

console.log(
  `[${failures === 0 ? 'PASS' : 'FAIL'}] voice lint: ${pagesChecked} prose pages checked; ` +
    `${ALLOWLIST.size} allowlisted (about); card pages excluded; ${failures} page(s) with first-person singular`,
);
if (pagesChecked === 0) {
  console.error('[FAIL] voice lint: no pages found; run astro build first');
  process.exit(1);
}
process.exit(failures === 0 ? 0 : 1);
