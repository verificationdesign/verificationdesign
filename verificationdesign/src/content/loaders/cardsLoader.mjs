import { readdir, readFile, stat } from 'node:fs/promises';
import { join, dirname, resolve, relative } from 'node:path';
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

function extractTitle(content) {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : null;
}

function extractIntent(content) {
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

function extractCategory(content) {
  const match = content.match(/^\*\((\w+ Pattern)\)\*\s*$/m);
  if (!match) return null;
  return CATEGORY_FROM_SUBTITLE[match[1]] || null;
}

function extractRelated(content) {
  const match = content.match(/##\s+Related Patterns\s*\n([\s\S]*?)(?=\n##\s|\n*$)/);
  if (!match) return [];
  const block = match[1];
  const names = [];
  const re = /\*\*([^*]+)\*\*/g;
  let m;
  while ((m = re.exec(block)) !== null) {
    names.push(m[1].trim());
  }
  return names;
}

function linkRelatedPatterns(content, linksByTitle) {
  return content.replace(
    /(##\s+Related Patterns\s*\n)([\s\S]*?)(?=\n##\s|\n*$)/,
    (_match, heading, block) => {
      const linkedBlock = block.replace(/\*\*([^*]+)\*\*/g, (bold, name) => {
        const href = linksByTitle.get(name.trim().toLowerCase());
        return href ? `[**${name}**](${href})` : bold;
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
        const stats = await stat(filePath);

        const title = extractTitle(content);
        const category = extractCategory(content);

        if (!title || !category) {
          logger.warn(`cardsLoader: skipping ${file} (missing title or category subtitle)`);
          continue;
        }

        const slug = file.replace(/\.md$/, '');
        if (allowlist && !allowlist.has(slug)) {
          continue;
        }

        cardInputs.push({ file, filePath, content, stats, title, category, slug });
        linksByTitle.set(title.toLowerCase(), `/patterns/${category}/${slug}/`);
      }

      for (const input of cardInputs) {
        const { filePath, content, stats, title, category, slug } = input;
        const id = `${category}/${slug}`;
        const updated = stats.mtime.toISOString().split('T')[0];
        const related = extractRelated(content);
        const intent = extractIntent(content);
        const renderedContent = linkRelatedPatterns(content, linksByTitle);

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
