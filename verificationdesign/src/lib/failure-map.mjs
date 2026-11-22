export const FAILURE_MAP = [
  {
    failure: 'The agent says done, but the work is not actually done.',
    shape: 'The workflow has no external signal for completion.',
    links: [
      { label: 'Executable Analog', href: '/patterns/verification/executable-analog/' },
      { label: 'Comparator', href: '/patterns/verification/comparator/' },
      { label: 'Fault Seed', href: '/patterns/verification/fault-seed/' },
      { label: 'Constitution', href: '/patterns/context-and-state/constitution/' },
    ],
  },
  {
    failure: 'The agent reviews itself and misses obvious problems.',
    shape: 'The verifier is too close to the generator.',
    links: [
      { label: 'Blind Oracle', href: '/patterns/verification/blind-oracle/' },
      { label: 'Cross-Family', href: '/patterns/orchestration/cross-family/' },
      { label: 'Adversary', href: '/patterns/orchestration/adversary/' },
      { label: 'Admissibility Gate', href: '/patterns/verification/admissibility-gate/' },
    ],
  },
  {
    failure: 'The same prompt produces different outcomes across runs.',
    shape: 'Variance is leaking through sampling, state, timing, or judge behavior.',
    links: [
      { label: 'State Baseline', href: '/patterns/context-and-state/state-baseline/' },
      { label: 'Judge Harness', href: '/patterns/verification/judge-harness/' },
      { label: 'Backpressure', href: '/patterns/orchestration/backpressure/' },
    ],
  },
  {
    failure: 'The check passes because the environment already looked right.',
    shape: 'The verifier observes a true fact, but not causality.',
    links: [
      { label: 'Delta', href: '/patterns/verification/delta/' },
      { label: 'Causal Tag', href: '/patterns/context-and-state/causal-tag/' },
      { label: 'Trajectory Cursor', href: '/patterns/context-and-state/trajectory-cursor/' },
    ],
  },
  {
    failure: 'Agents disagree, loop, or escalate randomly.',
    shape: 'The system has no explicit routing policy for uncertainty.',
    links: [
      { label: 'Escalation Chain', href: '/patterns/orchestration/escalation-chain/' },
      { label: 'Debate', href: '/patterns/orchestration/debate/' },
      { label: 'Backpressure', href: '/patterns/orchestration/backpressure/' },
    ],
  },
  {
    failure: 'Tool calls are messy, unsafe, or hard to verify.',
    shape: 'The boundary between model intent, tool input, and policy is ambiguous.',
    links: [
      { label: 'Guardrail Decorator', href: '/patterns/context-and-state/guardrail-decorator/' },
      { label: 'Tool Adapter', href: '/patterns/orchestration/tool-adapter/' },
      { label: 'Constitution', href: '/patterns/context-and-state/constitution/' },
    ],
  },
];
