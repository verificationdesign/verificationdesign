export const REPO_URL = 'https://github.com/verificationdesign/verificationdesign';

export function cardSourceUrl(slug: string): string {
  return `${REPO_URL}/blob/main/ai-design-patterns/cards/${slug}.md`;
}

export const REPO_ISSUES_URL = `${REPO_URL}/issues/new`;
