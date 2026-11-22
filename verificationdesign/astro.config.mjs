import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import sitemap from '@astrojs/sitemap';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  site: 'https://verificationdesign.com',
  trailingSlash: 'always',
  vite: {
    define: {
      __VERIFICATIONDESIGN_ROOT__: JSON.stringify(fileURLToPath(new URL('.', import.meta.url))),
    },
  },
  redirects: {
    '/patterns/verification/adversarial-frame/': '/patterns/verification/admissibility-gate/',
  },
  integrations: [
    mdx(),
    sitemap({
      filter: (page) => !page.includes('/book'),
    }),
  ],
  markdown: {
    shikiConfig: {
      themes: {
        light: 'github-light-high-contrast',
        dark: 'github-dark',
      },
      wrap: true,
    },
  },
  build: {
    format: 'directory',
  },
});
