export const DEFAULT_LOCALE = 'en';

export const ui = {
  en: {
    siteName: 'Verification Design',
    nav: {
      primary: 'Primary',
      patterns: 'Patterns',
      principles: 'Principles',
      references: 'References',
      about: 'About',
    },
    routes: {
      home: '/',
      patterns: '/patterns/',
      principles: '/principles/',
      references: '/references/',
      about: '/about/',
      book: '/book/',
    },
    principles: {
      patterns: 'Patterns',
    },
    card: {
      breadcrumbRoot: 'Patterns',
      navigation: 'Pattern navigation',
      previous: 'Previous',
      next: 'Next',
      sections: 'Sections in this pattern',
      updated: 'Updated',
      viewSource: 'View source',
      markdown: 'Markdown',
      principles: 'Principles',
      reportError: 'Report an error',
    },
    copy: {
      label: 'Copy code to clipboard',
      idle: 'Copy',
      copied: 'Copied',
      failed: 'Failed',
    },
    footer: {
      updated: 'Patterns updated',
      updatedFallback: 'Patterns updated recently.',
      repo: 'Source, checks, and history on GitHub',
      agents: 'For agents:',
      agentIndex: 'index',
      fullCorpus: 'full corpus',
      license: 'Written content CC BY 4.0. Card code samples CC0. Site code MIT.',
    },
  },
} as const;

export type Locale = keyof typeof ui;

export function getUi(locale: Locale = DEFAULT_LOCALE) {
  return ui[locale];
}
