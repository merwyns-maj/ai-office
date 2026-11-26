# engine/runtime

Loads an office folder, validates it against `engine/schema/office.md` (v0) and shows what the next run would do. Python 3.11, standard library only. Read-only: no file writes, no SDK, no network, no credentials. Live agent runs are T-024.

Run from the repo root (`<office>` is an office id such as `ai-office`, or a path to an office folder):

```bash
python -m engine.runtime validate <office>   # exit 0 clean, 1 problems, 2 usage / office not found
python -m engine.runtime dry-run  <office>   # validates first, then prints the next task's run plan
```

Dry-run picks the highest priority (P0 first), then the lowest task number. It skips terminal tasks, tasks whose `depends_on` are not `done` (a cross-office dependency counts as not done), and tasks owned by `human`.

## Office chat helper (T-063)

```bash
python -m engine.runtime chat plan|reply|status|purge|rules|mentions ai-office   # JSON or text on stdin, JSON on stdout
```

`chat.py` is pure (no file or network access). Chat text is company data: the CLI reads stdin and prints to stdout, never write its output into this repo. Format and procedure: `engine/schema/chat.md` and pmo-playbook section 9.

## Tests

```bash
python -m unittest -v
```

Runs everything (parser, loader and validation defects, dry-run pick rules, no-SDK/no-network/read-only checks) and exits 0 on a clean checkout.
