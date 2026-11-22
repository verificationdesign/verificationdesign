export const PRINCIPLE_MAP = [
  { number: 1, anchor: 'external-signals', title: 'External signals over self-review', cards: ['executable-analog', 'guardrail-decorator', 'adversary', 'evidence-manifest'] },
  { number: 2, anchor: 'independence', title: 'Independence between generation and verification', cards: ['blind-oracle', 'escalation-chain'] },
  { number: 3, anchor: 'step-level', title: 'Step-level checkpoints', cards: ['trajectory-cursor', 'backpressure', 'effect-witness'] },
  { number: 4, anchor: 'adversarial-framing', title: 'Adversarial framing', cards: ['admissibility-gate', 'adversary'] },
  { number: 5, anchor: 'explicit-criteria', title: 'Explicit criteria', cards: ['constitution', 'comparator', 'admissibility-gate'] },
  { number: 6, anchor: 'executable-verification', title: 'Executable verification is king', cards: ['executable-analog', 'comparator', 'tool-adapter', 'backpressure', 'guardrail-decorator', 'fault-seed'] },
  { number: 7, anchor: 'cross-family', title: 'Cross-family beats self-verification', cards: ['cross-family', 'judge-harness'] },
  { number: 8, anchor: 'simulate-debate', title: 'Simulate debate', cards: ['debate'] },
  { number: 9, anchor: 'isolate-ambient-state', title: 'Isolate verification from ambient state', cards: ['delta', 'state-baseline', 'causal-tag'] },
];

/** @param {string[]} cardSlugs */
export function validatePrincipleMap(cardSlugs) {
  const mapped = new Set(PRINCIPLE_MAP.flatMap((principle) => principle.cards));
  const available = new Set(cardSlugs);
  const unknown = [...mapped].filter((slug) => !available.has(slug));
  const unmapped = cardSlugs.filter((slug) => !mapped.has(slug));
  const empty = PRINCIPLE_MAP.filter((principle) => !principle.cards.length);
  if (unknown.length || unmapped.length || empty.length) {
    throw new Error(
      `Invalid principle map: unknown cards [${unknown.join(', ')}], ` +
      `unmapped cards [${unmapped.join(', ')}], ` +
      `principles without cards [${empty.map((principle) => principle.number).join(', ')}]`,
    );
  }
}
