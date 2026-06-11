import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

type ReferenceSource = {
  title: string;
  href: string;
};

export type ReferenceEntry = {
  key: string;
  label: string;
  href: string;
  sources: ReferenceSource[];
};

type ReferenceInput = {
  title: string;
  href: string;
  body: string;
};

const ARXIV_RE = /\barXiv:(\d{4}\.\d{4,5})(?:v\d+)?\b/g;
const MARKDOWN_LINK_RE = /\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g;
const SOURCE_LINK_ANCHOR_RE = /<a\b[^>]*class="source-link"[^>]*>/g;
const HREF_ATTR_RE = /href="(https?:\/\/[^"]+)"/;
const ARIA_LABEL_ATTR_RE = /aria-label="Source:\s*([^"]+)"/;
const ARXIV_ABS_HREF_RE = /^https:\/\/arxiv\.org\/abs\/(\d{4}\.\d{4,5})/;

// Site prose pages that cite via superscript source-link anchors.
const PROSE_PAGES: Array<{ file: string; source: ReferenceSource }> = [
  { file: 'src/pages/index.astro', source: { title: 'Home', href: '/' } },
  { file: 'src/pages/about.astro', source: { title: 'About', href: '/about/' } },
  { file: 'src/pages/principles.astro', source: { title: 'Principles', href: '/principles/' } },
];

function evidenceSection(markdown: string): string {
  const match = markdown.match(/##\s+Evidence\s*\n([\s\S]*?)(?=\n##\s|\n*$)/);
  return match ? match[1] : '';
}

function normalizeHref(href: string): string {
  return href
    .trim()
    .replace(/^https:\/\/arxiv\.org\/html\//, 'https://arxiv.org/abs/')
    .replace(/\/$/, '');
}

function addReference(
  references: Map<string, ReferenceEntry>,
  label: string,
  href: string,
  source: ReferenceSource,
) {
  const normalized = normalizeHref(href);
  const key = normalized.toLowerCase();
  const existing = references.get(key);

  if (existing) {
    if (!existing.sources.some((s) => s.href === source.href)) {
      existing.sources.push(source);
    }
    return;
  }

  references.set(key, {
    key,
    label: label.trim(),
    href: normalized,
    sources: [source],
  });
}

function collectFromMarkdown(
  references: Map<string, ReferenceEntry>,
  markdown: string,
  source: ReferenceSource,
) {
  let linkMatch;
  while ((linkMatch = MARKDOWN_LINK_RE.exec(markdown)) !== null) {
    addReference(references, linkMatch[1], linkMatch[2], source);
  }

  let arxivMatch;
  while ((arxivMatch = ARXIV_RE.exec(markdown)) !== null) {
    const id = arxivMatch[1];
    addReference(references, `arXiv:${id}`, `https://arxiv.org/abs/${id}`, source);
  }
}

function collectFromSourceLinks(
  references: Map<string, ReferenceEntry>,
  html: string,
  source: ReferenceSource,
) {
  let anchorMatch;
  while ((anchorMatch = SOURCE_LINK_ANCHOR_RE.exec(html)) !== null) {
    const href = anchorMatch[0].match(HREF_ATTR_RE)?.[1];
    if (!href) continue;
    const arxivId = href.match(ARXIV_ABS_HREF_RE)?.[1];
    const label = arxivId
      ? `arXiv:${arxivId}`
      : (anchorMatch[0].match(ARIA_LABEL_ATTR_RE)?.[1] ?? href);
    addReference(references, label, href, source);
  }
}

export async function collectReferences(cards: ReferenceInput[]): Promise<ReferenceEntry[]> {
  const references = new Map<string, ReferenceEntry>();

  for (const card of cards) {
    collectFromMarkdown(references, evidenceSection(card.body), {
      title: card.title,
      href: card.href,
    });
  }

  const canonicalPath = resolve(process.cwd(), '../verification_design.md');
  const canonical = await readFile(canonicalPath, 'utf8');
  const referencesTable = canonical.match(/## References\s*\n([\s\S]*)$/)?.[1] ?? '';
  collectFromMarkdown(references, referencesTable, {
    title: 'Verification Design Principles',
    href: '/principles/',
  });

  for (const page of PROSE_PAGES) {
    const pageSource = await readFile(resolve(process.cwd(), page.file), 'utf8');
    collectFromSourceLinks(references, pageSource, page.source);
  }

  return Array.from(references.values()).sort((a, b) => a.label.localeCompare(b.label));
}
