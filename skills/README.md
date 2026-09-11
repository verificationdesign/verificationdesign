# Verification skills

Two self-contained Agent Skills apply the Verification Design methodology to an
operator's artifact. `verification-design` writes a design and numbered verification requirements with
checks, justified by recorded catalog applicability judgments. `verification-audit` checks an existing artifact
against nine principles and reports evidence, defects and uncertainty, with catalog
routing and no fix proposals. Scripts validate and render records so their shape is
consistent across hosts. They do not decide whether a judgment is true.

## Install

Python 3.11 or later is required; every script uses only the standard library.
A startup guard refuses older Python versions with exit 2; `--check` reports the version.
Clone or download this repository, then copy the two skill directories into the
host's skills directory. For example, from a clone into a Claude Code project:

```bash
mkdir -p /path/to/project/.claude/skills
cp -R skills/verification-design skills/verification-audit /path/to/project/.claude/skills/
```

| Host | Target directory | Status |
|---|---|---|
| Claude Code | `.claude/skills/` | Tested; this version does not scan `.agents/skills/` |
| Codex | `.agents/skills/` or `~/.agents/skills/` | Tested at project and user scope |
| Copilot | Host-specific skills directory | Untested; explicit-only guarantee unsupported |

Each copied directory includes its own scripts, references and catalog snapshot.
Do not install duplicate copies through both manual copying and another package manager.

Optional, for users who already have Node.js and want the skills CLI:

```bash
npx skills add verificationdesign/verificationdesign --skill verification-design --skill verification-audit
```

The optional installer adds a Node.js dependency; clone-and-copy does not require Node.js.

## Invoke and configure

Claude Code: `/verification-design` and `/verification-audit`.
Codex: `$verification-design` and `$verification-audit`.
Append a scope, such as `the local release script's completion check`. The artifact
defaults to the current working tree, with a path or URL in the invocation or
conversation overriding it. Scope comes from the invocation or conversation. If
missing, the skill asks exactly one question and waits. It echoes both inputs.

The shipped default is explicit-only invocation. To re-enable model-triggered
activation in your installed copy, make the one edit for your host:

- Claude Code: delete the top-level `disable-model-invocation: true` line from SKILL.md.
- Codex: set `policy.allow_implicit_invocation: true` in `agents/openai.yaml`.

`metadata.disable-model-invocation: "true"` is the portable statement of the shipped
preference. The two tested hosts use their own controls above. The repository checker
enforces the shipped defaults; an installed copy may differ.

## Guarantee scope

Observed invocation-control results recorded by the maintainer on 2026-09-08 and 2026-09-10:

| Host | Version | Scan path | Explicit-only enforced | Date |
|---|---|---|---|---|
| Claude Code | 2.1.263, 2.1.265, 2.1.267 | `.claude/skills/` | yes (tests 1 to 4) | 2026-09-08, 2026-09-10 |
| Codex CLI | 0.153.4 | `.agents/skills/`, `~/.agents/skills/` | yes, both scopes | 2026-09-08 |
| Antigravity CLI | 1.2.0 | `.agents/skills/` (ran from it) | not supported: the host strips the front matter, passes no skill directory, and omits a project-installed skill from its skills list, so the model searched the home folder to find the package; works when the prompt names the skill directory | 2026-09-10 |
| Copilot | not tested | | unsupported | |

Other hosts are untested and may model-activate the skill. The probes observed hidden
catalog entries, working explicit invocation and no implicit invocation, with an
unflagged control activating. This table describes host invocation controls, not the
correctness of these skills' judgments. Blind task-level tests (fixture artifacts only,
records and expected outputs withheld) passed on Claude Code and Codex for v1.0.0 and
v1.1.0 on 2026-09-08 and for v1.2.0 on 2026-09-10 (five fixtures); the maintainer
judged each output against the fixture's required result.
The maintainer reruns blind host tests for each release before tagging it; the
compatibility line names only versions on which the probes were actually rerun.

SKILL.md is an ordinary readable file. The invocation flag does not prevent a model
from opening it as a file. The package carries one non-spec top-level field,
`disable-model-invocation`, because Claude Code requires it for the observed behavior.
The spec reference validator rejects that field; the optional checker validates a
temporary copy with exactly that one top-level line removed and verifies the difference.

## Corpus and offline behavior

Release `skills/v1.2.0` pins `corpus/v1.0.0`, revision
`e632a86b2ca8fbb7f83b3130ba083784c7817667`. The packaged catalog is the only catalog
used for decisions. A live drift report never replaces it. See [CHANGELOG.md](CHANGELOG.md).

Validation, routing and rendering need no network. Catalog-only operation retains
intent, applicability conditions, determinism moves, observable signals and the failure
map, but not full card or Principles prose. Use `VERIFICATION_SKILLS_OFFLINE=1` or
`load_catalog.py fetch ... --offline` to disable optional retrieval. Retrieval is
otherwise attempted only by an explicit fetch or drift command. Source text is fetched
from commit-pinned raw URLs and accepted only after its normalized hash matches.
Unavailable text is recorded with its URL and reason and stays visible in uncertainty.
Nothing is cached. The `--base-url` loopback override and `--live-url` exist for tests.

Run commands from the installed skill directory. Scripts offer `--help`, never prompt,
and use exit codes 0 (ok), 2 (usage), 3 (validation), 4 (unavailable), 5 (internal).
Stdout is JSON; text retrieval and markdown rendering use a `text` envelope with
`--output -`. With `--output FILE`, the file contains source text or markdown, and
stdout reports the destination. Output files are written only at the requested path,
and a path that resolves to the script's input record or to a file inside the skill
directory is refused with exit 2 before anything is written.

From this repository, run `python3 scripts/check_skills.py`. The checker verifies
pins against git, fixtures and loopback retrieval tests. `--links` adds live checks;
`--skills-ref` adds the external spec reference validator. Neither is used in CI.

The installed package carries no tests or fixtures; those and `check_skills.py` live
only in the publishing repository and are not portable. An installed copy can check
its pins with `load_catalog.py --check` and its records with the validators. Compare
its files against the tagged repository tree to establish whether it matches a release;
nothing in the package performs that comparison.

## Record helpers and output location

- `scripts/scaffold_record.py`: emit an unfilled record from the catalog or checklist,
  with counts; fill and validate it before rendering. The scaffold carries a `skill`
  object naming the package, its version and its pinned hashes (catalog, Principles
  and, for the audit skill, the question checklist); validation requires an exact match,
  and every rendered document states them, so a reader knows which question set judged it.
- Every record names the generator and verifier model families in `models`, with
  `unknown` written explicitly when a family is not recorded.
- `scripts/check_citations.py`: check evidence citation file existence and line bounds,
  without judging what the cited text means; several `--root` arguments are allowed,
  first file match wins, so order them deliberately. Repeated citations are reported
  for operator review and do not fail the check.

Records and outputs go in a dated directory the operator can see, beside the artifact
or where the operator says, never in system temp storage or inside the skill directory.

## License

Skill code is MIT. Catalog content is CC BY 4.0, attributed to
Verification Design (verificationdesign.com). See the repository's
[code license](../LICENSE) and [content license](../LICENSE-CONTENT.md).
