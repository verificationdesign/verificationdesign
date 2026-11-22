import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdir, readFile, readdir, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import {
  cardAllowlist,
  cardUpdated,
  extractCategory,
  extractIntent,
  extractRelated,
  extractTitle,
} from '../src/content/loaders/cardsLoader.mjs';
import { READING_ORDER } from '../src/lib/reading-order.mjs';
import { FAILURE_MAP } from '../src/lib/failure-map.mjs';
import { collectReferences } from '../src/lib/references.ts';
import { REPO_URL } from '../src/lib/repo.ts';

const SITE = 'https://verificationdesign.com';
const REPO = resolve(process.cwd(), '..');
const REVISION = process.env.GITHUB_SHA || execFileSync('git', ['rev-parse', 'HEAD'], { cwd: REPO, encoding: 'utf8' }).trim();
const sha256 = (body) => createHash('sha256').update(body).digest('hex');
const CARDS_DIR = join(REPO, 'ai-design-patterns/cards');
const DIST = resolve(process.cwd(), process.env.SITE_OUTPUT_DIR || 'dist');
const LICENSE = 'CC BY 4.0';
const RAW_PRINCIPLES_URL = `${REPO_URL.replace('https://github.com/', 'https://raw.githubusercontent.com/')}/${REVISION}/verification_design.md`;
const CATEGORY_LABELS = {
  'context-and-state': 'Context and State Patterns',
  verification: 'Verification Patterns',
  orchestration: 'Orchestration Patterns',
};

function normalizeBody(value) {
  return `${value.replace(/\r\n/g, '\n').replace(/\n*$/, '')}\n`;
}

function extractSection(body, heading) {
  const escaped = heading.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = body.match(new RegExp(`^## ${escaped}\\s*\\n([\\s\\S]*?)(?=^## |(?![\\s\\S]))`, 'm'));
  return match?.[1]?.trim() ?? '';
}

function firstParagraph(body, heading) {
  return extractSection(body, heading).split(/\n\s*\n/)[0];
}

function bullets(body, heading) {
  return [...extractSection(body, heading).matchAll(/^[*-] (.+(?:\n[ \t]+.+)*)/gm)]
    .map((match) => match[1].replace(/\*\*|\*|`/g, '').replace(/\s+/g, ' ').trim().replace(/;$/, ''));
}

function sortKeys(value) {
  if (Array.isArray(value)) return value.map(sortKeys);
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, sortKeys(value[key])]));
  }
  return value;
}

function quote(value) {
  return `"${String(value).replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
}

function frontmatter(fields, related) {
  const lines = ['---'];
  for (const [key, value] of Object.entries(fields)) {
    lines.push(value === true ? `${key}: true` : `${key}: ${quote(value)}`);
  }
  if (related !== undefined) {
    lines.push('related:');
    for (const item of related) {
      lines.push(`  - title: ${quote(item.title)}`);
      lines.push(`    url: ${quote(item.url)}`);
    }
  }
  return `${lines.join('\n')}\n---\n\n`;
}

async function emit(relativePath, contents) {
  const outputPath = join(DIST, relativePath);
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, contents.replace(/\r\n/g, '\n'), 'utf8');
}

const cardFiles = (await readdir(CARDS_DIR)).filter((file) => file.endsWith('.md'));
const cards = [];
for (const file of cardFiles) {
  const body = await readFile(join(CARDS_DIR, file), 'utf8');
  const title = extractTitle(body);
  const category = extractCategory(body);
  const intent = extractIntent(body);
  if (!title || !category || !intent) continue;
  const slug = file.replace(/\.md$/, '');
  cards.push({
    id: `${category}/${slug}`,
    file,
    source: `ai-design-patterns/cards/${file}`,
    body: normalizeBody(body),
    title,
    category,
    slug,
    intent,
    relatedNames: extractRelated(body),
  });
}

const byId = new Map(cards.map((card) => [card.id, card]));
const byTitle = new Map(cards.map((card) => [card.title, card]));
const fullOrder = READING_ORDER.map((id) => {
  const card = byId.get(id);
  if (!card) throw new Error(`Reading order names missing card: ${id}`);
  return card;
});
if (fullOrder.length !== cards.length) {
  throw new Error(`Reading order has ${fullOrder.length} cards; filesystem has ${cards.length}`);
}

const allowlist = cardAllowlist();
const orderedCards = fullOrder.filter(({ slug }) => !allowlist || allowlist.has(slug));
const selectedIds = new Set(orderedCards.map(({ id }) => id));
const selectedHrefs = new Set(orderedCards.map(({ id }) => `/patterns/${id}/`));
const patternLabel = (label, href) => selectedHrefs.has(href)
  ? `[${label}](${SITE}${href.replace(/\/$/, '.md')})`
  : label;

const failureSection = [
  '## Start from the failure',
  '',
  'First the pain, then the pattern. Each failure lists the patterns to reach for, closest fit first.',
  '',
  ...FAILURE_MAP.flatMap((entry) => [
    `### ${entry.failure}`,
    '',
    entry.shape,
    '',
    ...entry.links.map((link) => `- ${patternLabel(link.label, link.href)}`),
    '',
  ]),
  `If the failure is still unclear, start with ${patternLabel('Constitution', '/patterns/context-and-state/constitution/')}. Most verification failures become easier to diagnose once the system has an explicit answer to what is being checked.`,
  '',
];

function selectedRelated(card) {
  return card.relatedNames.flatMap((title) => {
    const target = byTitle.get(title);
    if (!target) throw new Error(`${card.file} names unknown related pattern: ${title}`);
    return selectedIds.has(target.id) ? [target] : [];
  });
}

const twins = [];
function registerTwin(path, canonical) {
  twins.push({ path: `/${path}`, canonical });
}

const principlesBody = normalizeBody(await readFile(join(REPO, 'verification_design.md'), 'utf8'));
await emit('principles.md', `${frontmatter({
  title: 'Verification Design Principles',
  canonical: `${SITE}/principles/`,
  source: 'verification_design.md',
  source_url: RAW_PRINCIPLES_URL,
  scope: 'The complete reference document; the HTML Principles page is a shorter, illustrated overview.',
  license: LICENSE,
})}${principlesBody}`);
registerTwin('principles.md', `${SITE}/principles/`);

for (const card of orderedCards) {
  const markdownUrl = `${SITE}/patterns/${card.category}/${card.slug}.md`;
  const canonical = `${SITE}/patterns/${card.category}/${card.slug}/`;
  const related = selectedRelated(card).map((target) => ({
    title: target.title,
    url: `${SITE}/patterns/${target.id}.md`,
  }));
  await emit(`patterns/${card.category}/${card.slug}.md`, `${frontmatter({
    title: card.title,
    canonical,
    source: card.source,
    source_url: `${REPO_URL.replace('https://github.com/', 'https://raw.githubusercontent.com/')}/${REVISION}/${card.source}`,
    updated: cardUpdated(join(CARDS_DIR, card.file)),
    license: LICENSE,
  }, related)}${card.body}`);
  registerTwin(`patterns/${card.category}/${card.slug}.md`, canonical);
  card.markdownUrl = markdownUrl;
  card.canonical = canonical;
}

const indexBody = [
  '# Patterns',
  '',
  ...orderedCards.map((card) => `- [${card.title}](${card.markdownUrl}): ${card.intent}`),
  '',
  ...failureSection,
].join('\n');
await emit('patterns.md', `${frontmatter({
  title: 'Patterns',
  canonical: `${SITE}/patterns/`,
  license: LICENSE,
  generated: true,
})}${indexBody}`);
registerTwin('patterns.md', `${SITE}/patterns/`);

for (const [category, title] of Object.entries(CATEGORY_LABELS)) {
  const body = [
    `# ${title}`,
    '',
    ...orderedCards
      .filter((card) => card.category === category)
      .map((card) => `- [${card.title}](${card.markdownUrl}): ${card.intent}`),
    '',
  ].join('\n');
  const canonical = `${SITE}/patterns/`;
  await emit(`patterns/${category}.md`, `${frontmatter({
    title,
    canonical,
    license: LICENSE,
    generated: true,
  })}${body}`);
  registerTwin(`patterns/${category}.md`, canonical);
}

const references = await collectReferences(orderedCards.map((card) => ({
  title: card.title,
  href: `/patterns/${card.category}/${card.slug}/`,
  body: card.body,
})));
const formatReferences = (includeContext) => [
  '# References',
  '',
  ...references.map((reference) => {
    const sources = reference.sources.map((source) => `[${source.title}](${new URL(source.href, SITE)})`).join(', ');
    return `- ${includeContext ? reference.context ?? '' : ''}[${reference.label}](${reference.href}): Cited from ${sources}.`;
  }),
  '',
].join('\n');
await emit('references.md', `${frontmatter({
  title: 'References',
  canonical: `${SITE}/references/`,
  license: LICENSE,
  generated: true,
})}${formatReferences(true)}`);
registerTwin('references.md', `${SITE}/references/`);

const llms = [
  '# Verification Design',
  '',
  '> Sourced principles and executable, stdlib-only Python pattern cards for verifying agent work: designing evals, checking tool-use output, and replacing self-review with external signals. Use when an agent must check its own or another agent\'s work.',
  '',
  'Content is licensed under CC BY 4.0. Markdown links provide reference documents and generated indexes for the corresponding HTML pages.',
  '',
  '## Available representations',
  '',
  `- [llms.txt](${SITE}/llms.txt): This index. Fetch first.`,
  `- [llms-full.txt](${SITE}/llms-full.txt): The full corpus in one plain-text file: principles, all cards in reading order, references. Fetch when you need everything.`,
  `- [catalog.json](${SITE}/catalog.json): Versioned routing manifest with revision and content hashes; per-card title, intent, URLs, related cards, first-paragraph determinism move, observable signal report fields, use_when and do_not_use_when lists, pattern_example and evidence_count coverage, plus the failure map. Coverage records are not research approval. Fetch to pick one card without loading the corpus.`,
  `- [patterns.md](${SITE}/patterns.md): Pattern index with the failure map. Fetch to choose a pattern from a symptom.`,
  `- [context-and-state.md](${SITE}/patterns/context-and-state.md): Index of the Context and State cards.`,
  `- [verification.md](${SITE}/patterns/verification.md): Index of the Verification cards.`,
  `- [orchestration.md](${SITE}/patterns/orchestration.md): Index of the Orchestration cards.`,
  `- [principles.md](${SITE}/principles.md): The complete reference document; the HTML Principles page is a shorter, illustrated overview.`,
  `- [references.md](${SITE}/references.md): Deduplicated sources.`,
  '',
  '## Principles',
  '',
  `- [Verification Design Principles](${SITE}/principles.md): The complete reference document; the HTML Principles page is a shorter, illustrated overview.`,
  `- [Raw principles source](${RAW_PRINCIPLES_URL}): The repository source file, raw markdown.`,
  '',
  ...Object.entries(CATEGORY_LABELS).flatMap(([category, title]) => [
    `## ${title}`,
    '',
    ...orderedCards
      .filter((card) => card.category === category)
      .map((card) => `- [${card.title}](${card.markdownUrl}): ${card.intent}`),
    '',
  ]),
  '## References',
  '',
  `- [References](${SITE}/references.md): Deduplicated sources and the pages that cite them.`,
  '',
  '## Source',
  '',
  `- [Repository](${REPO_URL}): Source repository.`,
  '- [License](https://creativecommons.org/licenses/by/4.0/): CC BY 4.0.',
  '',
  '## Optional',
  '',
  `- [About](${SITE}/about/): A human-facing introduction for operators.`,
  '',
].join('\n');
await emit('llms.txt', llms);

const fullBlocks = [
  { canonical: `${SITE}/principles/`, source: 'verification_design.md', body: principlesBody },
  ...orderedCards.map((card) => ({ canonical: card.canonical, source: card.source, body: card.body })),
  { canonical: `${SITE}/references/`, source: 'generated', body: formatReferences(false) },
];
const full = fullBlocks.map((block) => [
  '---',
  `Canonical: ${block.canonical}`,
  `Source: ${block.source}`,
  '',
  block.body.replace(/\n$/, ''),
  '',
].join('\n')).join('\n');
await emit('llms-full.txt', full);

const catalog = {
  schema_version: 1,
  revision: REVISION,
  content_sha256: sha256(orderedCards.map((card) => card.body).join('')),
  generated: true,
  license: LICENSE,
  site: SITE,
  principles: {
    html_url: `${SITE}/principles/`,
    markdown_url: `${SITE}/principles.md`,
    source_url: RAW_PRINCIPLES_URL,
  },
  cards: orderedCards.map((card) => ({
    id: card.id,
    category: card.category,
    title: card.title,
    intent: card.intent,
    html_url: card.canonical,
    markdown_url: card.markdownUrl,
    source_url: `${REPO_URL.replace('https://github.com/', 'https://raw.githubusercontent.com/')}/${REVISION}/${card.source}`,
    related: selectedRelated(card).map(({ id }) => id),
    determinism_move: firstParagraph(card.body, 'Determinism Move'),
    observable_signal: bullets(card.body, 'Observable Signal'),
    use_when: bullets(card.body, 'Use When'),
    do_not_use_when: bullets(card.body, 'Do Not Use When'),
    pattern_example: /### Pattern[^\n]*\n(?:(?!\n###? )[^])*?```python\n/.test(card.body) ? 'executable' : 'none',
    evidence_count: bullets(card.body, 'Evidence').length,
    source_sha256: sha256(card.body),
  })),
  failures: FAILURE_MAP.map((entry) => ({
    failure: entry.failure,
    shape: entry.shape,
    cards: entry.links.filter(({ href }) => selectedHrefs.has(href)).map((link) => link.href.replace(/^\/patterns\//, '').replace(/\/$/, '')),
  })),
};
await emit('catalog.json', `${JSON.stringify(sortKeys(catalog), null, 2)}\n`);

const headerRules = twins.map((twin) => [
  twin.path,
  `  Link: <${twin.canonical}>; rel="canonical"`,
].join('\n')).join('\n\n');
const alternates = new Map();
for (const twin of twins) {
  const path = new URL(twin.canonical).pathname;
  if (!alternates.has(path)) alternates.set(path, []);
  alternates.get(path).push(`  Link: <${SITE}${twin.path}>; rel="alternate"; type="text/markdown"`);
}
const reverseRules = [...alternates].map(([path, links]) => [path, ...links].join('\n')).join('\n\n');
const staticHeaders = (await readFile(resolve(process.cwd(), 'public/_headers'), 'utf8'))
  .replace(/\r\n/g, '\n')
  .replace(/\n*$/, '\n');
await writeFile(join(DIST, '_headers'), `${staticHeaders}\n${headerRules}\n\n${reverseRules}\n`, 'utf8');

console.log(`Generated markdown twins: ${twins.length}`);
console.log(`Generated llms.txt card entries: ${orderedCards.length}`);
console.log(`Generated llms-full.txt content blocks: ${fullBlocks.length}`);
console.log(`Appended canonical header rules: ${twins.length}`);
console.log(`Appended alternate header links: ${twins.length} across ${alternates.size} HTML routes`);
