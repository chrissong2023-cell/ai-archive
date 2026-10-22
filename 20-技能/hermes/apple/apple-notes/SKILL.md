---
name: apple-notes
description: "Manage Apple Notes via memo CLI: create, search, edit."
version: 1.0.1
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Notes, Apple, macOS, note-taking]
    related_skills: [obsidian]
prerequisites:
  commands: [memo]
---

# Apple Notes

Use `memo` to manage Apple Notes directly from the terminal. Notes sync across all Apple devices via iCloud.

## Prerequisites

- **macOS** with Notes.app
- Install: `brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
- Grant Automation access to Notes.app when prompted (System Settings → Privacy → Automation)

## When to Use

- User asks to create, view, or search Apple Notes
- Saving information to Notes.app for cross-device access
- Organizing notes into folders
- Exporting notes to Markdown/HTML

## When NOT to Use

- Obsidian vault management → use the `obsidian` skill
- Bear Notes → separate app (not supported here)
- Quick agent-only notes → use the `memory` tool instead

## Quick Reference

### View Notes

```bash
memo notes                        # List all notes
memo notes -f "Folder Name"       # Filter by folder
memo notes -s "query"             # Search notes (fuzzy)
```

### Create Notes

```bash
memo notes -a                     # Add a note (opens your $EDITOR)
memo notes -a -f "Folder Name"    # Add a note into a specific folder
```

`-a`/`--add` is a bare flag — it opens your `$EDITOR` to compose the note; it does
not take a title argument. Use `-f/--folder` to target a folder. Set `$EDITOR`
first (e.g. `export EDITOR=vim`).

### Edit Notes

```bash
memo notes -e                     # Interactive selection to edit
```

### Delete Notes

```bash
memo notes -d                     # Interactive selection to delete
```

### Move Notes

```bash
memo notes -m                     # Move note to folder (interactive)
```

### Export Notes

```bash
memo notes -ex                    # Export to HTML/Markdown
```

## When Notes data is TCC-blocked (memo / AppleScript unavailable)

On macOS 15+, driving Notes via AppleEvents fails silently (-1712, no prompt) for hardened-runtime
ad-hoc-signed apps, and reading the Notes container returns `Operation not permitted`. In order:

1. **Try the container directly** — `~/Library/Group Containers/group.com.apple.notes/`. `ls -la <file>`
   (stat) succeeds even while TCC denies opens; `cp`/`dd` fail until the calling app holds **Full Disk
   Access**. Re-launching a script under another app (`open -a Terminal script.command`) only helps if
   that app itself has FDA — usually it does not.
2. **Query the DB** once readable: copy `NoteStore.sqlite` to scratch **together with `-wal` and `-shm`**,
   then `sqlite3`. Table `ZICCLOUDSYNCINGOBJECT` holds everything:
   - notes: `Z_ENT=12`, title in `ZTITLE1`, text in `ZADDITIONALINDEXABLETEXT` / `ZSNIPPET`
   - attachments: `Z_ENT=5`, `ZTYPEUTI` like `com.apple.m4a-audio` / `com.apple.paper`, `ZNOTE` → note PK, `ZMEDIA` → media row PK
   - media rows: `Z_ENT=11`, `ZIDENTIFIER` = the folder name under `Accounts/<acct>/Media/`
   Timestamps are Core Data epoch (2001-01-01).
3. **Audio attachments** sit at `Accounts/<acct>/Media/<media-uuid>/1_<uuid>/recording.m4a`. One recording
   is often duplicated across several notes (or several notes share a title) — dedupe by md5 before transcribing.
4. **Handwriting / drawings** are `com.apple.paper` attachments; the rendered pages are at
   `Accounts/<acct>/FallbackImages/<ident>/*/FallbackImage.png` and `Previews/<ident>-768x768-*/Preview.png`.
   The sibling `.bundle/` dirs hold vector strokes only — read the PNGs.
5. **AirDrop receipts do not always land in `~/Downloads`.** Check
   `log show --last 10m --predicate 'process == "sharingd"'` before telling the user their transfer is missing.

## Transcribing recordings pulled out of Notes

Recordings exported from a Notes container are ordinary m4a files. The full pipeline (300 s chunking,
`-mc 0 -et 2.8`, SRT merge offsets, two-model cross-check, minutes delivery) lives in the
**`client-meeting-minutes`** skill — follow it there instead of re-deriving the flags. Two Notes-specific bits:

- Models on this machine: `~/.hermes/models/ggml-large-v3-turbo.bin` (fast, whole file) and
  `ggml-large-v3.bin` (≈1× realtime, only for critical 5-minute windows); anything missing comes from
  `https://hf-mirror.com/ggerganov/whisper.cpp/resolve/main/<file>` (huggingface.co is unreachable here).
- Dedupe by md5 before transcribing — one recording is often stored once per duplicated note, so an
  8-file attachment list can turn out to be 1 recording plus 1 handwriting page replicated 3 times.

## Limitations

- Cannot edit notes containing images or attachments
- Interactive prompts require terminal access (use pty=true if needed)
- macOS only — requires Apple Notes.app

## Rules

1. Prefer Apple Notes when user wants cross-device sync (iPhone/iPad/Mac)
2. Use the `memory` tool for agent-internal notes that don't need to sync
3. Use the `obsidian` skill for Markdown-native knowledge management
