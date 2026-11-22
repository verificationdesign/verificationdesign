import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFile, readdir } from 'node:fs/promises';
import { join, relative, resolve, sep } from 'node:path';

const SITE = 'https://verificationdesign.com';
// Fixture: the only GitHub origin any generated link may point at.
const REPO_FIXTURE = 'https://github.com/verificationdesign/verificationdesign';
const RAW_FIXTURE = 'https://raw.githubusercontent.com/verificationdesign/verificationdesign/';
const REPO = resolve(process.cwd(), '..');
const REVISION = process.env.GITHUB_SHA || execFileSync('git', ['rev-parse', 'HEAD'], { cwd: REPO, encoding: 'utf8' }).trim();
const sha256 = (body) => createHash('sha256').update(body).digest('hex');
const CARDS_DIR = join(REPO, 'ai-design-patterns/cards');
const DIST = resolve(process.cwd(), 'dist');
const ORDER = [
  'context-and-state/constitution',
  'context-and-state/guardrail-decorator',
  'context-and-state/causal-tag',
  'context-and-state/trajectory-cursor',
  'context-and-state/evidence-manifest',
  'context-and-state/state-baseline',
  'verification/executable-analog',
  'verification/blind-oracle',
  'verification/comparator',
  'verification/delta',
  'verification/judge-harness',
  'verification/admissibility-gate',
  'verification/fault-seed',
  'orchestration/cross-family',
  'orchestration/adversary',
  'orchestration/debate',
  'orchestration/escalation-chain',
  'orchestration/backpressure',
  'orchestration/tool-adapter',
  'orchestration/effect-witness',
];
const CATEGORY = {
  'Context Pattern': 'context-and-state',
  'Verification Pattern': 'verification',
  'Orchestration Pattern': 'orchestration',
};
const FIXED = ['principles.md', 'patterns.md', 'patterns/context-and-state.md',
  'patterns/verification.md', 'patterns/orchestration.md', 'references.md'];
const errors = [];

function fail(message) {
  errors.push(message);
}

function normalizeBody(value) {
  return `${value.replace(/\r\n/g, '\n').replace(/\n*$/, '')}\n`;
}

function unquote(value, context) {
  if (!/^"(?:[^"\\]|\\["\\])*"$/.test(value)) {
    fail(`${context}: invalid double-quoted scalar`);
    return '';
  }
  return value.slice(1, -1).replace(/\\(["\\])/g, '$1');
}

function parseTwin(contents, path) {
  const normalized = contents.replace(/\r\n/g, '\n');
  if (!normalized.startsWith('---\n')) {
    fail(`${path}: missing opening frontmatter delimiter`);
    return { data: {}, related: [], body: normalized };
  }
  const end = normalized.indexOf('\n---\n', 4);
  if (end < 0) {
    fail(`${path}: missing closing frontmatter delimiter`);
    return { data: {}, related: [], body: '' };
  }
  const lines = normalized.slice(4, end).split('\n');
  const data = {};
  const related = [];
  let inRelated = false;
  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    if (line === 'related:') {
      if (inRelated || Object.hasOwn(data, 'related')) fail(`${path}: duplicate related key`);
      data.related = true;
      inRelated = true;
      continue;
    }
    if (inRelated && line.startsWith('  - title: ')) {
      const title = unquote(line.slice(11), `${path} related title`);
      const urlLine = lines[i + 1] ?? '';
      if (!urlLine.startsWith('    url: ')) {
        fail(`${path}: related title lacks paired URL`);
      } else {
        related.push({ title, url: unquote(urlLine.slice(9), `${path} related URL`) });
        i += 1;
      }
      continue;
    }
    inRelated = false;
    const scalar = line.match(/^([a-z_]+): (.+)$/);
    if (!scalar) {
      fail(`${path}: invalid frontmatter line: ${line}`);
      continue;
    }
    const [, key, raw] = scalar;
    if (Object.hasOwn(data, key)) fail(`${path}: duplicate frontmatter key: ${key}`);
    if (key === 'generated' && raw === 'true') data[key] = true;
    else data[key] = unquote(raw, `${path} ${key}`);
  }
  const bodyStart = end + 5;
  if (normalized[bodyStart] !== '\n') fail(`${path}: frontmatter must be followed by one blank line`);
  return { data, related, body: normalized.slice(bodyStart + 1) };
}

async function walkMarkdown(directory) {
  const found = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) found.push(...await walkMarkdown(path));
    else if (entry.name.endsWith('.md')) found.push(relative(DIST, path).split(sep).join('/'));
  }
  return found.sort();
}

const cards = [];
for (const file of (await readdir(CARDS_DIR)).filter((name) => name.endsWith('.md')).sort()) {
  const sourceBody = await readFile(join(CARDS_DIR, file), 'utf8');
  const title = sourceBody.match(/^#\s+(.+)$/m)?.[1]?.trim();
  const subtitle = sourceBody.match(/^\*\(([^)]+ Pattern)\)\*\s*$/m)?.[1];
  const category = CATEGORY[subtitle];
  if (!title || !category) continue;
  const slug = file.replace(/\.md$/, '');
  cards.push({
    id: `${category}/${slug}`,
    title,
    category,
    slug,
    file,
    source: `ai-design-patterns/cards/${file}`,
    sourceBody: normalizeBody(sourceBody),
    intent: (sourceBody.match(/^## Intent\s*\n+([^\n]+)/m)?.[1] ?? '').replace(/[*`]/g, '').trim().replace(/\s+/g, ' '),
  });
}
const byId = new Map(cards.map((card) => [card.id, card]));
const byTitle = new Map(cards.map((card) => [card.title, card]));
const fixtureMissing = ORDER.filter((id) => !byId.has(id));
const fixtureExtra = cards.filter((card) => !ORDER.includes(card.id)).map((card) => card.id);
if (fixtureMissing.length || fixtureExtra.length) {
  fail(`reading-order membership mismatch; missing=${fixtureMissing.join(',') || 'none'} extra=${fixtureExtra.join(',') || 'none'}`);
}
console.log(`Check 11 reading-order fixture: fixture=${ORDER.length} filesystem=${cards.length} missing=${fixtureMissing.length} extra=${fixtureExtra.length}`);

const cardPaths = cards.map((card) => `patterns/${card.category}/${card.slug}.md`);
const expected = new Set([...FIXED, ...cardPaths]);
const actual = await walkMarkdown(DIST);
const missing = [...expected].filter((path) => !actual.includes(path));
const unexpected = actual.filter((path) => !expected.has(path));
for (const path of missing) fail(`missing expected twin: ${path}`);
for (const path of unexpected) fail(`unexpected markdown twin: ${path}`);
console.log(`Check 1 expected twins present: expected=${expected.size} found=${actual.filter((path) => expected.has(path)).length} missing=${missing.length}`);
console.log(`Check 2 unexpected twins absent: markdown_files=${actual.length} unexpected=${unexpected.length}`);

const parsed = new Map();
let metadataCompared = 0;
let bodiesCompared = 0;
let relatedResolved = 0;
for (const path of actual.filter((item) => expected.has(item))) {
  parsed.set(path, parseTwin(await readFile(join(DIST, path), 'utf8'), path));
}
const canonicalFor = (path) => {
  if (path === 'principles.md') return `${SITE}/principles/`;
  if (path === 'patterns.md') return `${SITE}/patterns/`;
  if (path === 'references.md') return `${SITE}/references/`;
  const categoryIndex = path.match(/^patterns\/([^/]+)\.md$/)?.[1];
  if (categoryIndex) return `${SITE}/patterns/`;
  return `${SITE}/${path.replace(/\.md$/, '/')}`;
};
for (const [path, twin] of parsed) {
  metadataCompared += 1;
  if (twin.data.canonical !== canonicalFor(path)) fail(`${path}: wrong canonical`);
  if (twin.data.license !== 'CC BY 4.0') fail(`${path}: wrong or missing license`);
  const card = cards.find((item) => path === `patterns/${item.category}/${item.slug}.md`);
  if (path === 'principles.md') {
    if (twin.data.source_url !== `${RAW_FIXTURE}${REVISION}/verification_design.md`) fail(`${path}: wrong source_url`);
    if (twin.data.scope !== 'The complete reference document; the HTML Principles page is a shorter, illustrated overview.') fail(`${path}: wrong scope`);
    if (twin.data.source !== 'verification_design.md') fail(`${path}: wrong source`);
    const source = normalizeBody(await readFile(join(REPO, 'verification_design.md'), 'utf8'));
    bodiesCompared += 1;
    if (normalizeBody(twin.body) !== source) fail(`${path}: body differs from source`);
  } else if (card) {
    if (twin.data.source_url !== `${RAW_FIXTURE}${REVISION}/${card.source}`) fail(`${path}: wrong source_url`);
    let expectedDate;
    try {
      expectedDate = execFileSync('git', ['log', '-1', '--format=%cI', '--', card.source], { cwd: REPO, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim().split('T')[0];
    } catch { /* Check archives against the build-date fallback. */ }
    expectedDate ||= new Date().toISOString().split('T')[0];
    if (twin.data.updated !== expectedDate) fail(`${path}: wrong updated date`);
    if (twin.data.source !== card.source) fail(`${path}: wrong source`);
    bodiesCompared += 1;
    if (normalizeBody(twin.body) !== card.sourceBody) fail(`${path}: body differs from source`);
    const relatedBlock = card.sourceBody.match(/##\s+Related Patterns\s*\n([\s\S]*?)(?=\n##\s|\n*$)/)?.[1] ?? '';
    const relatedNames = [...relatedBlock.matchAll(/\*\*([^*]+)\*\*/g)]
      .map((match) => match[1].trim().replace(/:$/, ''));
    const predicted = relatedNames.map((title) => {
      const target = byTitle.get(title);
      if (!target) {
        fail(`${path}: source names unknown related card ${title}`);
        return { title, url: '' };
      }
      return { title, url: `${SITE}/patterns/${target.category}/${target.slug}.md` };
    });
    relatedResolved += predicted.length;
    if (JSON.stringify(twin.related) !== JSON.stringify(predicted)) fail(`${path}: related pairs differ from source prediction`);
  } else if (twin.data.generated !== true) {
    fail(`${path}: generated twin lacks generated: true`);
  }
}
console.log(`Check 3 frontmatter metadata: parsed=${parsed.size} compared=${metadataCompared} malformed_errors=${errors.filter((e) => e.includes('frontmatter') || e.includes('canonical') || e.includes('source') || e.includes('license')).length}`);
console.log(`Check 4 source bodies: compared=${bodiesCompared} mismatches=${errors.filter((e) => e.includes('body differs')).length}`);
console.log(`Check 5 related mappings: card_twins=${cards.length} related_urls_resolved=${relatedResolved} mismatches=${errors.filter((e) => e.includes('related')).length}`);

const llmsText = (await readFile(join(DIST, 'llms.txt'), 'utf8')).replace(/\r\n/g, '\n');
const llmsLines = llmsText.split('\n');
const llmsLinks = [];
let inH2 = false;
let h2BodyLines = 0;
for (const line of llmsLines) {
  if (line.startsWith('## ')) { inH2 = true; continue; }
  if (!inH2 || line === '') continue;
  h2BodyLines += 1;
  const match = line.match(/^- \[[^\]]+\]\(([^)]+)\): .+$/);
  if (!match) fail(`llms.txt: invalid H2 body line: ${line}`);
  else llmsLinks.push(match[1]);
}
const internalMarkdown = llmsLinks
  .filter((url) => url.startsWith(`${SITE}/`) && url.endsWith('.md'))
  .map((url) => url.slice(SITE.length + 1));
const expectedLlms = new Set([...FIXED, ...cardPaths]);
for (const path of expectedLlms) {
  if (!internalMarkdown.includes(path)) fail(`llms.txt: omitted content twin ${path}`);
}
for (const path of internalMarkdown) {
  if (!expected.has(path)) fail(`llms.txt: link does not exist in dist: ${path}`);
}
for (const url of [`${SITE}/llms-full.txt`, `${SITE}/catalog.json`, `${SITE}/patterns.md`,
  `${SITE}/patterns/context-and-state.md`, `${SITE}/patterns/verification.md`, `${SITE}/patterns/orchestration.md`]) {
  if (!llmsLinks.includes(url)) fail(`llms.txt: omitted required representation ${url}`);
}
const githubLinks = llmsLinks.filter((url) => /github(usercontent)?\.com/.test(url));
for (const url of githubLinks) {
  if (!(url === REPO_FIXTURE || url.startsWith(`${REPO_FIXTURE}/`) || url.startsWith(RAW_FIXTURE))) fail(`llms.txt: GitHub link outside repo fixture: ${url}`);
}
console.log(`Check 6b llms.txt repo links: github_links=${githubLinks.length} outside_fixture=${githubLinks.filter((url) => !(url === REPO_FIXTURE || url.startsWith(`${REPO_FIXTURE}/`) || url.startsWith(RAW_FIXTURE))).length}`);
console.log(`Check 6 llms.txt: H2_body_lines=${h2BodyLines} linked_entries=${llmsLinks.length} internal_twins=${internalMarkdown.length} required_twins=${expectedLlms.size}`);

const fullText = (await readFile(join(DIST, 'llms-full.txt'), 'utf8')).replace(/\r\n/g, '\n');
const blockRe = /(?:^|\n)---\nCanonical: ([^\n]+)\nSource: ([^\n]+)\n\n/g;
const blocks = [...fullText.matchAll(blockRe)];
const expectedCanonicals = [
  `${SITE}/principles/`,
  ...ORDER.map((id) => `${SITE}/patterns/${id}/`),
  `${SITE}/references/`,
];
const observedCanonicals = blocks.map((match) => match[1]);
if (JSON.stringify(observedCanonicals) !== JSON.stringify(expectedCanonicals)) fail('llms-full.txt: missing or incorrectly ordered content blocks');
const frontmatterBlocks = (fullText.match(/^---\n(?:title|canonical|source|license|generated|related):/gm) ?? []).length;
if (frontmatterBlocks) fail('llms-full.txt: contains a YAML frontmatter block');
console.log(`Check 7 llms-full.txt: blocks=${blocks.length} expected=${expectedCanonicals.length} frontmatter_blocks=${frontmatterBlocks}`);

const generatedFiles = [...actual.map((path) => join(DIST, path)), join(DIST, 'llms.txt'), join(DIST, 'llms-full.txt')];
let emDashCount = 0;
for (const path of generatedFiles) emDashCount += ((await readFile(path, 'utf8')).match(/\u2014/g) ?? []).length;
if (emDashCount) fail(`generated files contain ${emDashCount} em dashes`);
console.log(`Check 8 em dashes: files_scanned=${generatedFiles.length} observed=${emDashCount}`);

const htmlFiles = [];
async function walkHtml(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name);
    if (entry.isDirectory()) await walkHtml(path);
    else if (entry.name.endsWith('.html')) htmlFiles.push(path);
  }
}
await walkHtml(DIST);
const expectedAlternate = new Map([
  ['principles/index.html', '/principles.md'],
  ['patterns/index.html', '/patterns.md'],
  ['references/index.html', '/references.md'],
  ...cards.map((card) => [`patterns/${card.category}/${card.slug}/index.html`, `/patterns/${card.category}/${card.slug}.md`]),
]);
let alternateLinks = 0;
for (const htmlPath of htmlFiles) {
  const relativePath = relative(DIST, htmlPath).split(sep).join('/');
  const html = await readFile(htmlPath, 'utf8');
  const found = [...html.matchAll(/<link\s+rel="alternate"\s+type="text\/markdown"\s+href="([^"]+)"\s*\/?>/g)].map((match) => match[1]);
  alternateLinks += found.length;
  const expectedHref = expectedAlternate.get(relativePath);
  if (expectedHref && JSON.stringify(found) !== JSON.stringify([expectedHref])) fail(`${relativePath}: missing or wrong markdown alternate`);
  if (!expectedHref && found.length) fail(`${relativePath}: unexpected markdown alternate`);
}
console.log(`Check 9 HTML alternates: html_pages=${htmlFiles.length} twin_pages=${expectedAlternate.size} alternate_links=${alternateLinks}`);

const headers = (await readFile(join(DIST, '_headers'), 'utf8')).replace(/\r\n/g, '\n');
const ruleRe = /^(\/[^\n]+\.md)\n  Link: <([^>]+)>; rel="canonical"$/gm;
const headerRules = [...headers.matchAll(ruleRe)].map((match) => ({ path: match[1].slice(1), canonical: match[2] }));
for (const path of expected) {
  const rule = headerRules.find((item) => item.path === path);
  if (!rule) fail(`_headers: missing canonical rule for ${path}`);
  else if (rule.canonical !== canonicalFor(path)) fail(`_headers: wrong canonical for ${path}`);
}
for (const rule of headerRules) {
  if (!expected.has(rule.path)) fail(`_headers: canonical rule for non-twin ${rule.path}`);
}
console.log(`Check 10 canonical headers: expected=${expected.size} found=${headerRules.length} unexpected=${headerRules.filter((rule) => !expected.has(rule.path)).length}`);

const reverseLinks = [];
let headerPath = '';
for (const line of headers.split('\n')) {
  if (line.startsWith('/')) headerPath = line;
  const match = line.match(/^  Link: <([^>]+)>; rel="alternate"; type="text\/markdown"$/);
  if (match) reverseLinks.push([headerPath, match[1]]);
}
const wantedReverse = [...expected].map((path) => [new URL(canonicalFor(path)).pathname, `${SITE}/${path}`]);
if (JSON.stringify(reverseLinks.map(JSON.stringify).sort()) !== JSON.stringify(wantedReverse.map(JSON.stringify).sort())) fail('_headers: reverse alternate links differ');
console.log(`Check 10 reverse headers: expected=${expected.size} found=${reverseLinks.length}`);

function decodeHtml(value) {
  return value.replace(/&#(\d+);/g, (_, code) => String.fromCodePoint(Number(code)))
    .replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'").replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
}

function sectionText(body, heading) {
  const start = body.indexOf(`## ${heading}\n`);
  if (start < 0) return '';
  const contentStart = start + heading.length + 4;
  const end = body.indexOf('\n## ', contentStart);
  return body.slice(contentStart, end < 0 ? undefined : end).trim();
}

function sectionBullets(body, heading) {
  const result = [];
  for (const line of sectionText(body, heading).split('\n')) {
    if (/^[*-] /.test(line)) result.push(line.slice(2));
    else if (/^[ \t]+\S/.test(line) && result.length) result[result.length - 1] += ` ${line.trim()}`;
  }
  return result.map((text) => text.replace(/[*`]/g, '').replace(/\s+/g, ' ').replace(/;\s*$/, '').trim());
}

function sorted(value) {
  if (Array.isArray(value)) return value.map(sorted);
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map((key) => [key, sorted(value[key])]));
  return value;
}

const homeHtml = decodeHtml(await readFile(join(DIST, 'index.html'), 'utf8'));
const patternsHtml = decodeHtml(await readFile(join(DIST, 'patterns/index.html'), 'utf8'));
let uniqueComparisons = 0;
let uniqueMismatches = 0;
for (const html of [homeHtml, patternsHtml]) {
  for (const card of cards) {
    uniqueComparisons += 1;
    const count = html.split(card.intent).length - 1;
    if (count !== 1) { uniqueMismatches += 1; fail(`intent uniqueness: ${card.id} occurs ${count} times`); }
  }
}
console.log(`Check 12 intent uniqueness: pages=2 comparisons=${uniqueComparisons} mismatches=${uniqueMismatches}`);

const compactPatternsHtml = patternsHtml.replace(/>\s+</g, '><');
const chooserMatch = compactPatternsHtml.match(/<div class="chooser-list">([\s\S]*?)<\/div><p class="chooser-footer">/);
const htmlFailures = [];
for (const match of (chooserMatch?.[1] ?? '').matchAll(/<section class="chooser-card"><h3>(.*?)<\/h3><p>(.*?)<\/p><ul role="list">([\s\S]*?)<\/ul><\/section>/g)) {
  htmlFailures.push({
    failure: match[1], shape: match[2],
    links: [...match[3].matchAll(/<li><a href="([^"]+)">(.*?)<\/a><\/li>/g)].map((link) => ({ href: link[1], label: link[2] })),
  });
}
const failureMarkdown = (parsed.get('patterns.md')?.body ?? '').split('\n## Start from the failure\n')[1] ?? '';
const mdFailures = [...failureMarkdown.matchAll(/### ([^\n]+)\n\n([^\n]+)\n\n([\s\S]*?)(?=\n### |\nIf the failure)/g)].map((match) => ({
  failure: match[1], shape: match[2],
  links: [...match[3].matchAll(/^- \[([^\]]+)\]\(([^)]+)\)$/gm)].map((link) => ({ label: link[1], href: link[2] })),
}));
const predictedFailures = htmlFailures.map((entry) => ({ ...entry, links: entry.links.map((link) => ({ label: link.label, href: `${SITE}${link.href.replace(/\/$/, '.md')}` })) }));
if (JSON.stringify(mdFailures) !== JSON.stringify(predictedFailures)) fail('patterns.md: failure section differs from built HTML chooser');
console.log(`Check 13 failure-section parity: html_failures=${htmlFailures.length} markdown_failures=${mdFailures.length} html_links=${htmlFailures.flatMap((entry) => entry.links).length}`);

let plainAlternates = 0;
let plainAlternateMismatches = 0;
for (const htmlPath of htmlFiles) {
  const found = [...(await readFile(htmlPath, 'utf8')).matchAll(/<link\s+rel="describedby"\s+href="([^"]+)"\s+title="llms\.txt"\s*\/?>/g)].map((match) => match[1]);
  plainAlternates += found.length;
  const rel = relative(DIST, htmlPath).split(sep).join('/');
  const wanted = rel === 'index.html' ? [`${SITE}/llms.txt`] : [];
  if (JSON.stringify(found) !== JSON.stringify(wanted)) { plainAlternateMismatches += 1; fail(`${rel}: wrong llms.txt alternate`); }
}
console.log(`Check 14 homepage llms.txt link: links=${plainAlternates} mismatched_pages=${plainAlternateMismatches}`);

const principlesSource = normalizeBody(await readFile(join(REPO, 'verification_design.md'), 'utf8'));
const referencesTwin = parsed.get('references.md');
const expectedFullBlocks = [
  { canonical: `${SITE}/principles/`, source: 'verification_design.md', body: principlesSource },
  ...ORDER.map((id) => { const card = byId.get(id); return { canonical: `${SITE}/patterns/${id}/`, source: card.source, body: card.sourceBody }; }),
  { canonical: `${SITE}/references/`, source: 'generated', body: normalizeBody(referencesTwin?.body ?? '') },
];
const expectedFull = normalizeBody(expectedFullBlocks.map((block) => ['---', `Canonical: ${block.canonical}`, `Source: ${block.source}`, '', block.body.replace(/\n$/, ''), ''].join('\n')).join('\n'));
if (normalizeBody(fullText) !== expectedFull) fail('llms-full.txt: exact normalized bytes differ');
console.log(`Check 15 llms-full.txt bytes: blocks_compared=${expectedFullBlocks.length} bytes=${Buffer.byteLength(expectedFull)} equal=${normalizeBody(fullText) === expectedFull}`);

const categoryLabels = { 'context-and-state': 'Context and State Patterns', verification: 'Verification Patterns', orchestration: 'Orchestration Patterns' };
const cardLine = (card) => `- [${card.title}](${SITE}/patterns/${card.category}/${card.slug}.md): ${card.intent}`;
const expectedLlmsText = [
  '# Verification Design', '',
  "> Sourced principles and executable, stdlib-only Python pattern cards for verifying agent work: designing evals, checking tool-use output, and replacing self-review with external signals. Use when an agent must check its own or another agent's work.", '',
  'Content is licensed under CC BY 4.0. Markdown links provide reference documents and generated indexes for the corresponding HTML pages.', '',
  '## Available representations', '',
  `- [llms.txt](${SITE}/llms.txt): This index. Fetch first.`,
  `- [llms-full.txt](${SITE}/llms-full.txt): The full corpus in one plain-text file: principles, all cards in reading order, references. Fetch when you need everything.`,
  `- [catalog.json](${SITE}/catalog.json): Versioned routing manifest with revision and content hashes; per-card title, intent, URLs, related cards, first-paragraph determinism move, observable signal report fields, use_when and do_not_use_when lists, pattern_example and evidence_count coverage, plus the failure map. Coverage records are not research approval. Fetch to pick one card without loading the corpus.`,
  `- [patterns.md](${SITE}/patterns.md): Pattern index with the failure map. Fetch to choose a pattern from a symptom.`,
  `- [context-and-state.md](${SITE}/patterns/context-and-state.md): Index of the Context and State cards.`,
  `- [verification.md](${SITE}/patterns/verification.md): Index of the Verification cards.`,
  `- [orchestration.md](${SITE}/patterns/orchestration.md): Index of the Orchestration cards.`,
  `- [principles.md](${SITE}/principles.md): The complete reference document; the HTML Principles page is a shorter, illustrated overview.`,
  `- [references.md](${SITE}/references.md): Deduplicated sources.`, '',
  '## Principles', '', `- [Verification Design Principles](${SITE}/principles.md): The complete reference document; the HTML Principles page is a shorter, illustrated overview.`,
  `- [Raw principles source](${RAW_FIXTURE}${REVISION}/verification_design.md): The repository source file, raw markdown.`, '',
  ...Object.entries(categoryLabels).flatMap(([category, title]) => [`## ${title}`, '', ...ORDER.map((id) => byId.get(id)).filter((card) => card.category === category).map(cardLine), '']),
  '## References', '', `- [References](${SITE}/references.md): Deduplicated sources and the pages that cite them.`, '',
  '## Source', '', `- [Repository](${REPO_FIXTURE}): Source repository.`, '- [License](https://creativecommons.org/licenses/by/4.0/): CC BY 4.0.', '',
  '## Optional', '', `- [About](${SITE}/about/): A human-facing introduction for operators.`, '',
].join('\n');
if (normalizeBody(llmsText) !== normalizeBody(expectedLlmsText)) fail('llms.txt: exact normalized bytes differ');
console.log(`Check 16 llms.txt bytes: card_lines=${cards.length} bytes=${Buffer.byteLength(normalizeBody(llmsText))} equal=${normalizeBody(llmsText) === normalizeBody(expectedLlmsText)}`);

const ordered = ORDER.map((id) => byId.get(id));
const expectedFlat = ['# Patterns', '', ...ordered.map(cardLine), ''];
const expectedFailureLines = ['## Start from the failure', '', 'First the pain, then the pattern. Each failure lists the patterns to reach for, closest fit first.', '', ...predictedFailures.flatMap((entry) => [`### ${entry.failure}`, '', entry.shape, '', ...entry.links.map((link) => `- [${link.label}](${link.href})`), '']), `If the failure is still unclear, start with [Constitution](${SITE}/patterns/context-and-state/constitution.md). Most verification failures become easier to diagnose once the system has an explicit answer to what is being checked.`, ''];
const expectedIndexes = new Map([['patterns.md', [...expectedFlat, ...expectedFailureLines].join('\n')], ...Object.entries(categoryLabels).map(([category, title]) => [`patterns/${category}.md`, [`# ${title}`, '', ...ordered.filter((card) => card.category === category).map(cardLine), ''].join('\n')])]);
let indexMismatches = 0;
for (const [path, body] of expectedIndexes) if (normalizeBody(parsed.get(path)?.body ?? '') !== normalizeBody(body)) { indexMismatches += 1; fail(`${path}: exact normalized bytes differ`); }
console.log(`Check 17 index twin bytes: files=${expectedIndexes.size} mismatches=${indexMismatches}`);

const expectedCatalog = sorted({ schema_version: 1, revision: REVISION, content_sha256: sha256(ordered.map((card) => card.sourceBody).join('')), generated: true, license: 'CC BY 4.0', site: SITE,
  principles: { html_url: `${SITE}/principles/`, markdown_url: `${SITE}/principles.md`, source_url: `${RAW_FIXTURE}${REVISION}/verification_design.md` },
  cards: ordered.map((card) => ({ id: card.id, category: card.category, title: card.title, intent: card.intent,
    html_url: `${SITE}/patterns/${card.id}/`, markdown_url: `${SITE}/patterns/${card.id}.md`, source_url: `${RAW_FIXTURE}${REVISION}/${card.source}`,
    related: [...(card.sourceBody.match(/##\s+Related Patterns\s*\n([\s\S]*?)(?=\n##\s|\n*$)/)?.[1] ?? '').matchAll(/\*\*([^*]+)\*\*/g)].map((match) => byTitle.get(match[1].trim().replace(/:$/, ''))?.id),
    determinism_move: sectionText(card.sourceBody, 'Determinism Move').split(/\n\s*\n/)[0], observable_signal: sectionBullets(card.sourceBody, 'Observable Signal'),
    use_when: sectionBullets(card.sourceBody, 'Use When'), do_not_use_when: sectionBullets(card.sourceBody, 'Do Not Use When'),
    pattern_example: (card.sourceBody.split(/^### Pattern[^\n]*\n/m)[1] ?? '').split(/^## /m)[0].includes('```python\n') ? 'executable' : 'none',
    evidence_count: sectionBullets(card.sourceBody, 'Evidence').length, source_sha256: sha256(card.sourceBody) })),
  failures: htmlFailures.map((entry) => ({ failure: entry.failure, shape: entry.shape, cards: entry.links.map((link) => link.href.replace(/^\/patterns\//, '').replace(/\/$/, '')) })),
});
const expectedCatalogText = `${JSON.stringify(expectedCatalog, null, 2)}\n`;
const catalogText = (await readFile(join(DIST, 'catalog.json'), 'utf8')).replace(/\r\n/g, '\n');
if (catalogText !== expectedCatalogText) fail('catalog.json: canonical bytes differ');
console.log(`Check 18 catalog.json bytes: cards=${expectedCatalog.cards.length} failures=${expectedCatalog.failures.length} bytes=${Buffer.byteLength(catalogText)} equal=${catalogText === expectedCatalogText}`);

const referenceMarkdownPairs = [...(referencesTwin?.body ?? '').matchAll(/^- \[([^\]]+)\]\(([^)]+)\):/gm)].map((match) => [match[1], match[2]]);
const referencesHtml = decodeHtml(await readFile(join(DIST, 'references/index.html'), 'utf8')).replace(/>\s+</g, '><');
const referenceHtmlPairs = [...referencesHtml.matchAll(/<li><a href="([^"]+)">(.*?)<\/a><span class="reference-sources">/g)].map((match) => [match[2], match[1]]);
if (JSON.stringify(referenceMarkdownPairs) !== JSON.stringify(referenceHtmlPairs)) fail('references.md: labels and links differ from HTML');
console.log(`Check 19 references parity: markdown=${referenceMarkdownPairs.length} html=${referenceHtmlPairs.length} equal=${JSON.stringify(referenceMarkdownPairs) === JSON.stringify(referenceHtmlPairs)}`);

if (errors.length) {
  for (const error of errors) console.error(`FAIL: ${error}`);
  console.error(`Markdown twin checks failed: ${errors.length}`);
  process.exit(1);
}
console.log('Markdown twin checks failed: 0');
