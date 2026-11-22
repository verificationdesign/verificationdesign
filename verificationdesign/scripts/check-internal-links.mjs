import { readFile, readdir, stat } from 'node:fs/promises';
import { join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { extractRelated, readCardCatalog } from '../src/content/loaders/cardsLoader.mjs';

const origin = 'https://verificationdesign.com';
const siteDir = fileURLToPath(new URL('../', import.meta.url));
const dist = resolve(siteDir, process.env.SITE_OUTPUT_DIR || 'dist');
const cardsDir = resolve(siteDir, '../ai-design-patterns/cards');
const failures = [];

function decodeAttribute(value) {
  return value.replace(/&(?:amp|quot|apos|lt|gt|#\d+|#x[\da-f]+);/gi, (entity) => {
    const name = entity.slice(1, -1).toLowerCase();
    if (name.startsWith('#')) {
      const code = name.startsWith('#x') ? parseInt(name.slice(2), 16) : Number(name.slice(1));
      return code > 0 && code <= 0x10ffff ? String.fromCodePoint(code) : '\ufffd';
    }
    return { amp: '&', quot: '"', apos: "'", lt: '<', gt: '>' }[name];
  });
}

function attributes(markup) {
  return new Map([...markup.matchAll(/([^\s=/>]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g)]
    .map(([, name, double, single, bare]) => [name.toLowerCase(), decodeAttribute(double ?? single ?? bare ?? '')]));
}

async function* htmlFiles(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) yield* htmlFiles(path);
    else if (entry.isFile() && entry.name.endsWith('.html')) yield path;
  }
}

const pages = new Map();
for await (const path of htmlFiles(dist)) {
  const source = '/' + relative(dist, path);
  const html = await readFile(path, 'utf8');
  const tags = [...html.matchAll(/<!--[\s\S]*?-->|<(script|style)\b((?:"[^"]*"|'[^']*'|[^'">])*)>([\s\S]*?)<\/\1\s*>|<([a-z][\w:-]*)\b((?:"[^"]*"|'[^']*'|[^'">])*)>/gi)]
    .filter((tag) => tag[1] || tag[4])
    .map(([, rawTag, rawAttrs, body, tag, attrs]) => ({
      name: (rawTag ?? tag).toLowerCase(),
      attrs: attributes(rawAttrs ?? attrs),
      body,
    }));
  pages.set(source, {
    html,
    tags,
    ids: new Set(tags.map(({ attrs }) => attrs.get('id')).filter(Boolean)),
    // Astro emits a refresh stub in dist for each configured redirect.
    redirect: tags.some(({ name, attrs }) =>
      name === 'meta' && attrs.get('http-equiv')?.toLowerCase() === 'refresh'),
  });
}

const cardSources = new Map();
const pathsByTitle = new Map();
for (const { category, slug, title, content } of await readCardCatalog(cardsDir)) {
  const path = `/patterns/${category}/${slug}/index.html`;
  pathsByTitle.set(title.toLowerCase(), path);
  cardSources.set(path, extractRelated(content));
}

let scanned = 0;
let redirects = 0;
let links = 0;
let fragments = 0;
let breadcrumbs = 0;
let expectedRelated = 0;
let linkedRelated = 0;
let plainRelated = 0;

function resolveHref(source, href) {
  const url = new URL(href, origin + source.replace(/\/index\.html$/, '/'));
  if (url.origin !== origin) return null;
  const path = url.pathname.split('/').map((part) => {
    const decoded = decodeURIComponent(part);
    if (decoded === '.' || decoded === '..' || /[/\\\0]/.test(decoded)) {
      throw new Error('invalid path segment');
    }
    return decoded;
  }).join('/');
  const file = path.endsWith('/') ? path + 'index.html' : path;
  return { file, fragment: decodeURIComponent(url.hash.slice(1)) };
}

const resolvedPaths = new Map();
async function resolveFile(file) {
  if (!resolvedPaths.has(file)) {
    let target = file;
    if (!pages.has(file)) {
      const entry = await stat(join(dist, file)).catch((error) => {
        if (error.code !== 'ENOENT' && error.code !== 'ENOTDIR') throw error;
        return null;
      });
      if (entry?.isDirectory()) target = file + '/index.html';
      if (!entry?.isFile() && !pages.has(target)) target = null;
    }
    resolvedPaths.set(file, target);
  }
  return resolvedPaths.get(file);
}

async function checkHref(source, href, breadcrumb = false) {
  try {
    const resolved = resolveHref(source, href);
    if (!resolved) return;
    if (breadcrumb) breadcrumbs++;
    else links++;
    if (resolved.fragment) fragments++;
    const file = await resolveFile(resolved.file);
    if (!file) throw new Error('missing target');
    const page = pages.get(file);
    if (resolved.fragment && page && !page.redirect && !page.ids.has(resolved.fragment)) {
      throw new Error(`missing id "${resolved.fragment}" in ${file}`);
    }
  } catch (error) {
    failures.push(`${source}: ${href}: ${error.message}`);
  }
}

for (const [source, page] of pages) {
  if (page.redirect) {
    redirects++;
    continue;
  }
  scanned++;
  for (const { name, attrs } of page.tags) {
    if (attrs.has('href') && (name === 'a' ||
        (name === 'link' && attrs.get('rel')?.toLowerCase().split(/\s+/).includes('alternate')))) {
      await checkHref(source, attrs.get('href'));
    }
  }

  if (!cardSources.has(source)) continue;
  for (const { name, attrs, body } of page.tags) {
    if (name !== 'script' || attrs.get('type') !== 'application/ld+json') continue;
    try {
      const data = JSON.parse(body);
      for (const entry of [data].flat()) {
        if (entry['@type'] !== 'BreadcrumbList') continue;
        for (const { item } of entry.itemListElement) {
          if (item !== undefined) await checkHref(source, item, true);
        }
      }
    } catch (error) {
      failures.push(`${source}: BreadcrumbList JSON-LD: ${error.message}`);
    }
  }

  const related = cardSources.get(source);
  const targets = related.map((name) => pathsByTitle.get(name.toLowerCase()));
  expectedRelated += targets.filter((path) => pages.has(path) && !pages.get(path).redirect).length;
  const list = page.html.match(/<h2\b[^>]*\bid="related-patterns"[^>]*>[\s\S]*?<\/h2>\s*<ul\b[^>]*>([\s\S]*?)<\/ul>/i);
  const items = [...(list?.[1] ?? '').matchAll(/<li\b[^>]*>([\s\S]*?)<\/li>/gi)];
  if (items.length !== related.length) {
    failures.push(`${source}: #related-patterns: expected ${related.length} items, found ${items.length}`);
  }
  for (const [index, [, item]] of items.entries()) {
    const name = related[index];
    const expectedTarget = targets[index];
    const shouldLink = pages.has(expectedTarget) && !pages.get(expectedTarget).redirect;
    const anchor = item.match(/^\s*<a\b([^>]*)>/i);
    const href = anchor && attributes(anchor[1]).get('href');
    let target;
    try {
      const resolved = href && resolveHref(source, href);
      if (resolved) target = await resolveFile(resolved.file);
    } catch {
      // The general href check reports malformed links with their source and href.
    }
    const label = item.match(/^\s*(?:<a\b[^>]*>)?<strong>([^<]+)<\/strong>/i)?.[1];
    const actualName = label && decodeAttribute(label).trim().replace(/:$/, '');
    if (!expectedTarget || actualName !== name) {
      failures.push(`${source}: #related-patterns: expected item ${name}, found ${actualName}`);
    } else if (shouldLink && target === expectedTarget) {
      linkedRelated++;
    } else if (shouldLink || anchor) {
      failures.push(`${source}: #related-patterns: ${name} must ${shouldLink ? `link to ${expectedTarget}` : 'be plain text'}`);
    } else {
      plainRelated++;
    }
  }
}

if (!scanned) failures.push('/: no built HTML pages found in dist');
for (const failure of failures) console.error(failure);
console.log(`Internal links: ${scanned} pages scanned, ${redirects} redirect stubs skipped, ${links} internal links checked, ${fragments} fragment links checked, ${breadcrumbs} JSON-LD URLs checked, Related Patterns linked ${linkedRelated} of ${expectedRelated}, ${plainRelated} shown as plain text, ${failures.length} failures.`);
process.exitCode = failures.length ? 1 : 0;
