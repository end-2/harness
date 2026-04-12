# Stage 1 — Scan: Detailed Behavior Rules

## Purpose

Build a complete picture of the project's filesystem layout, classify every file by role, identify entry points and configuration files, and determine whether lite or heavy analysis mode is appropriate. This stage produces the raw structural data that all subsequent stages consume.

## Execution sequence

1. **Validate target** — confirm `project_root` exists and is readable. If not, escalate immediately (see `references/escalation.md`).

2. **Load exclusion patterns** — combine:
   - `.gitignore` from `project_root` (if present)
   - Default exclusions: `node_modules/`, `.git/`, `__pycache__/`, `dist/`, `build/`, `vendor/`, `venv/`, `.venv/`, `.next/`, `.nuxt/`, `target/` (Rust/Java), `bin/` (Go), `coverage/`, `.cache/`, `.idea/`, `.vscode/`
   - User-supplied `--exclude` patterns

3. **Build directory tree** — walk `project_root` recursively, skipping excluded paths. Record:
   - Directory names and nesting depth
   - File names with extensions
   - Symbolic link targets (detect cycles — if a symlink points to an ancestor, skip it and note the cycle)

4. **Classify files** — assign each file to exactly one category:

   | Category | Signals |
   |----------|---------|
   | Source code | Known extensions: `.ts`, `.tsx`, `.js`, `.jsx`, `.py`, `.go`, `.rs`, `.java`, `.rb`, `.php`, `.c`, `.cpp`, `.h`, `.cs`, `.swift`, `.kt`, `.scala`, `.ex`, `.exs`, `.clj`, `.hs`, `.lua`, `.sh`, `.sql` |
   | Configuration | Manifest files, dotfiles (`.eslintrc`, `.prettierrc`), `tsconfig.json`, `webpack.config.*`, `vite.config.*`, `next.config.*`, `Makefile`, `Dockerfile`, `docker-compose.*`, `.env*`, `*.toml`, `*.ini`, `*.cfg` |
   | Test | Files matching `*_test.*`, `*.test.*`, `*.spec.*`, `test_*.*`, or under directories named `test/`, `tests/`, `__tests__/`, `spec/`, `specs/` |
   | Documentation | `.md`, `.rst`, `.txt` (in docs-like directories), `LICENSE`, `CHANGELOG`, `CONTRIBUTING` |
   | Build artifact | Files under `dist/`, `build/`, `out/`, `target/`, `.next/`, compiled outputs |
   | Static asset | Images (`.png`, `.jpg`, `.svg`, `.ico`), fonts (`.woff`, `.ttf`), stylesheets (`.css`, `.scss`, `.less`), HTML templates |

5. **Identify entry points** — look for files whose names or locations suggest they are application entry points:

   | Pattern | Typical role |
   |---------|-------------|
   | `main.*`, `index.*`, `app.*`, `server.*` | Application bootstrap |
   | `cmd/*/main.go` | Go CLI/service entry |
   | `src/main.rs`, `src/lib.rs` | Rust crate entry |
   | `manage.py`, `wsgi.py`, `asgi.py` | Python web app entry |
   | `bin/*`, `scripts/*` | Executable scripts |
   | Files with shebang lines (`#!/...`) | Executable scripts |
   | `Procfile`, `entrypoint.sh` | Container/deploy entry |

   Record each entry point with its inferred role and the evidence for that inference.

6. **Map configuration files** — for each config file found, tag its role:

   | File pattern | Role |
   |-------------|------|
   | `package.json`, `go.mod`, `Cargo.toml`, `pyproject.toml`, `requirements.txt`, `Gemfile`, `pom.xml`, `build.gradle` | Package manager / dependency manifest |
   | `tsconfig.json`, `babel.config.*`, `swc.*` | Compiler / transpiler |
   | `webpack.config.*`, `vite.config.*`, `rollup.config.*`, `esbuild.*` | Bundler |
   | `.eslintrc*`, `.prettierrc*`, `biome.json`, `ruff.toml` | Linter / formatter |
   | `jest.config.*`, `vitest.config.*`, `pytest.ini`, `setup.cfg [tool:pytest]` | Test framework |
   | `.github/workflows/*`, `.gitlab-ci.yml`, `Jenkinsfile`, `.circleci/*` | CI/CD |
   | `Dockerfile`, `docker-compose.*`, `*.Dockerfile` | Container |
   | `terraform/`, `*.tf`, `cloudformation.*`, `pulumi.*` | Infrastructure as Code |
   | `.env`, `.env.*` | Environment variables |

7. **Determine adaptive depth** — evaluate complexity metrics:

   | Metric | Lite threshold | Heavy threshold |
   |--------|---------------|-----------------|
   | Total source files | <= 50 | > 50 |
   | Distinct languages | 1 | > 1 |
   | Frameworks detected | <= 1 | > 1 |
   | Max directory depth | <= 3 | > 3 |

   If **all four** metrics fall within lite thresholds, select lite mode. Otherwise, select heavy mode. Record the metric values and the decision reasoning. The user can override with `--depth`.

8. **Compress tree for token efficiency** — produce a compact representation:
   - Group files with identical structure: `components/{Header,Footer,Nav,...12 more}/index.tsx`
   - Collapse directories with a single child: `src/utils/` instead of showing the intermediate
   - Show file counts for large directories: `migrations/ (47 files)`
   - Limit tree depth display: full detail for depth 1-3, summary for deeper levels

## Output

Pass the following to Stage 2:
- Compressed directory tree (string)
- File classification map (category -> file list)
- Entry points list (file, role, evidence)
- Config files list (file, role, evidence)
- Depth mode verdict (lite/heavy) with evidence
- Total file count by category
- Exclusion patterns applied

## Metadata operations

At this stage, no artifacts are written to disk yet. The scan results are held in working memory for subsequent stages. Artifact creation happens in Stage 4 (map).

## Script usage

No `artifact.py` calls in this stage. The scan is purely analytical.
