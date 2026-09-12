"""Deterministic header and source formatting for records."""
import sys
sys.dont_write_bytecode = True
from load_catalog import emit
import json


def header(title, record, catalog, meta):
    lines = ["# " + title, "", f'Artifact: {record["artifact"]}', "",
             f'Scope: {record["scope"]}', "", f'Corpus revision: `{catalog["revision"]}`', "",
             f'Corpus tag: `{meta["corpus-tag"]}`', ""]
    skill = record["skill"]
    pins = "; ".join(f'{key.removesuffix("_sha256")} `{value}`' for key, value in skill.items() if key.endswith("_sha256"))
    lines += [f'Skill: {skill["name"]} {skill["version"]}', "", f'Skill pins: {pins}', "",
              f'Generator model: {record["models"]["generator"]}', "", f'Verifier model: {record["models"]["verifier"]}', ""]
    if "artifact_identity" in record:
        identity = record["artifact_identity"]
        lines += [f'Artifact identity: revision {identity["revision"] or "not recorded"}; {len(identity["files"])} files', ""]
        lines += [f'- {f["path"]}: `{f["sha256"]}`' for f in identity["files"]] + [""]
    lines += ["## Assumptions", ""]
    lines += [f'- {x["topic"]}: {x["statement"]}' for x in record["assumptions"]] or ["None."]
    lines.append("")
    if "measurements" in record:
        lines += ["## Measurements", ""]
        for x in record["measurements"]:
            # The command goes in a fenced block so multi-line commands stay readable.
            lines += [f'- {x["id"]}: kind {x["kind"]}; env `{json.dumps(x["env"], sort_keys=True)}`; '
                      f'exit {x["exit_code"]}; artifact revision `{x["artifact_revision"]}`; '
                      f'log {x["log"] or "none"}; note: {x["note"]}', "",
                      "```text", x["command"], "```", ""]
        if not record["measurements"]:
            lines += ["None.", ""]
    return lines


def unavailable(record):
    lines = ["### Unavailable sources", ""] if record.get("unavailable_sources") else []
    for x in record.get("unavailable_sources", []):
        lines += ["```json", json.dumps(x, indent=2, ensure_ascii=False), "```", ""]
    return lines


class Sources:
    def __init__(self):
        self.definitions = {}

    def card(self, card):
        slug = card["id"].split("/")[-1]
        self.definitions[slug] = card["html_url"]
        self.definitions[slug + "-src"] = card["source_url"]
        return f'[{card["title"]}][{slug}] ([pinned source][{slug}-src])'

    def render(self, revision, principles):
        # The human-readable Principles page is always named, even when nothing routed to a card.
        definitions = {"principles": principles["html_url"], "principles-src": principles["source_url"]}
        definitions.update(self.definitions)
        return ["## Sources", "", f'Corpus revision: `{revision}`.', "",
                "Principles: [verificationdesign.com][principles] ([pinned source][principles-src]).", ""] + [
            f'[{key}]: {url}' for key, url in definitions.items()] + [""]
