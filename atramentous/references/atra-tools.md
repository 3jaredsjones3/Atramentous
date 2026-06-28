# Atramentous — platform notes

How to install and how each runtime invokes the skills. The unit of installation
is **one skill folder**, not the whole collection.

## Packaging

Each skill is a folder containing `SKILL.md` (the core skill also ships a
`references/` directory). The expected upload/drop unit is the folder, zipped:

```
atramentous.zip
└── atramentous/
    ├── SKILL.md
    └── references/
        ├── grammar.md
        └── atra-tools.md
```

Zip the **folder**, not the bare `SKILL.md` — the core skill references files in
`references/`, and zipping only the markdown breaks those links.

## Anthropic Cowork

Customize → upload one zip per skill. Cowork reads each `SKILL.md`'s `name` and
`description` and matches skills to a request semantically — you do not name a
skill every time. The persistent `atramentous` mode is the one you enable
explicitly (say "atramentous" or "use atramentous"); the companions
(`-weave`, `-review`, `-rehydrate`, `-reconcile`, `-map`) are matched on demand
or invoked by name. To force one: "use atra-review."

## Codex

Skills load natively from the skills directory. Drop each skill folder in. When a
skill activates, follow the instructions presented. The `description` trigger
phrases drive activation, same as Cowork.

## Claude Code

Place each skill folder in your skills directory and invoke via the `Skill`
tool, or let matching activate it. `~/.agents/skills/` works as a cross-runtime
alias on Codex / Copilot CLI / Gemini CLI.

## Project-level reinforcement

Atramentous pairs with a project's instructions file. If `AGENTS.md` /
`CLAUDE.md` / `GEMINI.md` already defines a marker vocabulary and a scaffolding
register (as the Zero Lagoon AGENTS.md does), Atramentous reuses it rather than
introducing a parallel system: the file's markers become the node `status`, the
file's register becomes the Atramentous register. Add one line to the
instructions file to make the mode sticky for that repo, e.g.:

```
This repository uses the Atramentous discipline. Treat the source tree as the
primary memory store: leave breadcrumbs and heavy nodes per the grammar, keep
docs/atramentous/register.md current, and run atra-rehydrate before
editing unfamiliar areas.
```

## Per-runtime tool vocabulary

The skills speak in actions ("grep the tree", "read the register", "open the
file", "run the tests") rather than naming one runtime's tools. Map them to your
runtime's equivalents (search, read, edit, shell). No skill assumes a specific
tool name.
