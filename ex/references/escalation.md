# Escalation Rules

Ex runs fully automatically and does not ask the user questions about code structure. However, certain situations make analysis physically impossible. In these cases — and only these — escalate to the user.

## Escalation triggers

### Critical (analysis cannot proceed)

| Situation | Detection | Escalation message |
|-----------|-----------|-------------------|
| **Target path does not exist** | `test -d "$1"` fails | "The specified project root `{path}` does not exist or is not a directory. Please provide a valid path." |
| **Target path is not readable** | Permission denied on traversal | "Cannot read the project at `{path}` — permission denied. Please check file permissions." |
| **Empty directory** | Zero files found after exclusion filtering | "The project at `{path}` appears to be empty (no files found after applying exclusion filters). Please verify this is the correct path." |
| **Binary-only project** | All files are binary (no text-based source code detected) | "The project at `{path}` contains only binary files — no parseable source code was found. Ex requires text-based source files to analyze." |

### Warning (analysis proceeds with degraded output)

These situations do **not** trigger escalation. Instead, note the limitation in the output and proceed:

| Situation | Handling |
|-----------|---------|
| **No manifest files found** | Proceed with file-extension-based language detection only. Note: "No package manifests found — tech stack detection is based on file extensions and code patterns only." |
| **Symbolic link cycle** | Skip the cyclic path, note it in the structure map: "Symbolic link cycle detected at `{path}` — skipped." |
| **Very large project (>10,000 files)** | Proceed but apply aggressive compression. Note: "Large project ({N} files) — output is heavily compressed to fit token budget." |
| **Mixed/ambiguous architecture** | Report all detected signals with confidence levels. Do not ask the user which style is "correct." |
| **Unrecognized language** | Classify as "source code (unknown language)" and skip framework detection for those files. |
| **Corrupted/unreadable individual files** | Skip them, note: "N files could not be read and were excluded from analysis." |
| **No .gitignore** | Use default exclusion patterns only. Proceed normally. |
| **Monorepo with many packages** | Analyze the full monorepo. Apply heavy mode. Note the package count. |

## Escalation format

When escalating, use this structure:

```
**Ex analysis cannot proceed.**

Reason: {clear explanation}
Path: {the project_root that was provided}
Suggestion: {what the user should do — fix permissions, provide a different path, etc.}
```

Do not escalate for analytical uncertainty. If you are unsure about architecture style, component boundaries, or technology versions — make your best inference, record the evidence and confidence level, and move on. The user hired Ex to figure things out from the code, not to ask them what the code does.
