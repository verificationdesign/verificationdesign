import { readdir, readFile } from 'node:fs/promises';
import { join, dirname, resolve, relative } from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
// Project root is four levels up from this loader file
// (loaders -> content -> src -> verificationdesign).
const PROJECT_ROOT = resolve(__dirname, '../../..');

const CATEGORY_FROM_SUBTITLE = {
  'Context Pattern': 'context-and-state',
  'Verification Pattern': 'verification',
  'Orchestration Pattern': 'orchestration',
};

const CATEGORY_LABEL = {
  'context-and-state': 'Context and State',
  'verification': 'Verification',
  'orchestration': 'Orchestration',
};

export function cardUpdated(filePath, warn = console.warn) {
  try {
    const date = execFileSync('git', ['log', '-1', '--format=%cI', '--', filePath], {
      cwd: dirname(filePath), encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'],
    }).trim();
    if (date && !Number.isNaN(Date.parse(date))) return date.split('T')[0];
  } catch { /* A source archive may have no git history. */ }
  warn(`cardsLoader: no git date for ${filePath}; using build date`);
  return new Date().toISOString().split('T')[0];
}

export function extractTitle(content) {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : null;
}

export function extractIntent(content) {
  const match = content.match(/##\s+Intent\s*\n+([\s\S]*?)(?=\n##\s|\n*$)/);
  if (!match) return null;
  const paragraph = match[1]
    .trim()
    .split(/\n\s*\n/)[0]
    .replace(/[*`]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  if (!paragraph) return null;
  const sentence = paragraph.match(/^.*?[.!?](?=\s|$)/);
  return sentence ? sentence[0] : paragraph;
}

export function extractCategory(content) {
  const match = content.match(/^\*\((\w+ Pattern)\)\*\s*$/m);
  if (!match) return null;
  return CATEGORY_FROM_SUBTITLE[match[1]] || null;
}

function relatedTitle(name) {
  return name.trim().replace(/:$/, '').trim();
}

export function extractRelated(content) {
  const match = content.match(/##\s+Related Patterns\s*\n([\s\S]*?)(?=\n##\s|\n*$)/);
  if (!match) return [];
  const block = match[1];
  const names = [];
  const re = /\*\*([^*]+)\*\*/g;
  let m;
  while ((m = re.exec(block)) !== null) {
    names.push(relatedTitle(m[1]));
  }
  return names;
}

function linkRelatedPatterns(content, linksByTitle, title) {
  return content.replace(
    /(##\s+Related Patterns\s*\n)([\s\S]*?)(?=\n##\s|\n*$)/,
    (_match, heading, block) => {
      const linkedBlock = block.replace(/\*\*([^*]+)\*\*/g, (bold, name) => {
        const target = relatedTitle(name);
        const relatedCard = linksByTitle.get(target.toLowerCase());
        if (!relatedCard) throw new Error(`${title} names unknown related pattern: ${target}`);
        if (!relatedCard.included) return bold;
        const start = name.indexOf(target);
        const suffix = name.slice(start + target.length);
        return `${name.slice(0, start)}[**${target}${suffix.trimEnd()}**](${relatedCard.href})${suffix.slice(suffix.trimEnd().length)}`;
      });
      return `${heading}${linkedBlock}`;
    },
  );
}

function cardAllowlist() {
  const raw = process.env.SITE_CARD_ALLOWLIST;
  if (!raw) return null;

  const slugs = raw
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

  return slugs.length ? new Set(slugs) : null;
}

export function cardsLoader({ sourcePath }) {
  const absoluteSource = resolve(__dirname, sourcePath);

  return {
    name: 'verification-design-cards',
    load: async ({ store, parseData, generateDigest, renderMarkdown, logger }) => {
      let files;
      try {
        files = await readdir(absoluteSource);
      } catch (err) {
        logger.warn(`cardsLoader: cannot read ${absoluteSource}: ${err.message}`);
        return;
      }

      const markdown = files.filter((f) => f.endsWith('.md'));
      const allowlist = cardAllowlist();
      store.clear();

      const cardInputs = [];
      const linksByTitle = new Map();

      for (const file of markdown) {
        const filePath = join(absoluteSource, file);
        const content = await readFile(filePath, 'utf8');

        const title = extractTitle(content);
        const category = extractCategory(content);

        if (!title || !category) {
          logger.warn(`cardsLoader: skipping ${file} (missing title or category subtitle)`);
          continue;
        }

        const slug = file.replace(/\.md$/, '');
        const included = !allowlist || allowlist.has(slug);
        linksByTitle.set(title.toLowerCase(), { href: `/patterns/${category}/${slug}/`, included });
        if (included) cardInputs.push({ file, filePath, content, title, category, slug });
      }

      for (const input of cardInputs) {
        const { filePath, content, title, category, slug } = input;
        const id = `${category}/${slug}`;
        const updated = cardUpdated(filePath, (message) => logger.warn(message));
        const related = extractRelated(content);
        const intent = extractIntent(content);
        const renderedContent = linkRelatedPatterns(content, linksByTitle, title);

        const data = await parseData({
          id,
          data: {
            slug,
            title,
            category,
            categoryLabel: CATEGORY_LABEL[category],
            updated,
            related,
            intent,
            sourceFile: filePath,
          },
        });

        const rendered = await renderMarkdown(renderedContent);

        store.set({
          id,
          data,
          body: content,
          filePath: relative(PROJECT_ROOT, filePath),
          digest: generateDigest(content),
          rendered,
        });
      }

      logger.info(`cardsLoader: loaded ${store.keys().length} cards from ${absoluteSource}`);
    },
  };
}
