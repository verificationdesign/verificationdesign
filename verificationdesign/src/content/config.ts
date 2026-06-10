import { defineCollection, z } from 'astro:content';
import { cardsLoader } from './loaders/cardsLoader.mjs';

const patterns = defineCollection({
  loader: cardsLoader({ sourcePath: '../../../../ai-design-patterns/cards' }),
  schema: z.object({
    slug: z.string(),
    title: z.string(),
    category: z.enum(['context-and-state', 'verification', 'orchestration']),
    categoryLabel: z.string(),
    updated: z.string(),
    related: z.array(z.string()).default([]),
    intent: z.string().nullable().optional(),
    sourceFile: z.string().optional(),
  }),
});

export const collections = { patterns };
