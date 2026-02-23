# Creating and Publishing the Documentation

This document explains how to install dependencies, preview the docs locally, publish them to GitHub Pages, and manage multiple language translations.

## Prerequisites

- Python ≥ 3.10
- A local clone of the repository

## Install Documentation Dependencies

Install the docs extra (includes `mkdocs`, `mkdocs-material`, and `mkdocstrings`):

```bash
pip install -e ".[docs]"
```

Or install them directly:

```bash
pip install mkdocs mkdocs-material "mkdocstrings[python]"
```

## Documentation Structure

The repository uses **one `mkdocs.yml` per language**, each pointing to its own `docs/` subdirectory:

| Config file | Language | Docs directory | Published at |
|---|---|---|---|
| `mkdocs.yml` | English (default) | `docs/` | `/merchnts-cp/` |
| `mkdocs.es.yml` | Spanish | `docs/es/` | `/merchnts-cp/es/` |

A language switcher (globe icon) is shown in the header of every page, linking between versions.

## Preview Locally

### English

Run the development server from the repository root:

```bash
mkdocs serve
```

This starts a live-reloading server at [http://127.0.0.1:8000](http://127.0.0.1:8000).

### Spanish

```bash
mkdocs serve -f mkdocs.es.yml
```

To bind to a different address or port:

```bash
mkdocs serve -f mkdocs.es.yml --dev-addr 0.0.0.0:8001
```

## Build the Static Site

### English

```bash
mkdocs build
```

Output is placed in `site/`.

### Spanish

```bash
mkdocs build -f mkdocs.es.yml -d site/es
```

### All languages

```bash
mkdocs build
mkdocs build -f mkdocs.es.yml -d site/es
```

> **Note:** `site/` is a build artifact and is excluded from version control via `.gitignore`.

## Publish to GitHub Pages

### Manual Deployment

Deploy the English docs first, then the Spanish docs into the `es/` subdirectory:

```bash
# Deploy English (creates/updates the gh-pages branch)
mkdocs gh-deploy

# Deploy Spanish into the es/ subdirectory
mkdocs gh-deploy -f mkdocs.es.yml -d site/es --remote-branch gh-pages
```

> **Important:** Always deploy English first — it sets up the `gh-pages` branch. Subsequent language deploys add their subdirectory without overwriting other languages.

### First-time GitHub Pages Setup

1. Go to your repository on GitHub.
2. Open **Settings → Pages**.
3. Under **Source**, select **Deploy from a branch**.
4. Select `gh-pages` as the branch and `/ (root)` as the folder.
5. Click **Save**.

Your docs will be available at:

- English: `https://mariofix.github.io/merchnts-cp/`
- Spanish: `https://mariofix.github.io/merchnts-cp/es/`

## Updating the Docs

1. Edit or add Markdown files in the appropriate `docs/` directory (`docs/` for English, `docs/es/` for Spanish).
2. Update the corresponding `mkdocs.yml` or `mkdocs.es.yml` if you add new pages to the `nav` section.
3. Preview with `mkdocs serve` (English) or `mkdocs serve -f mkdocs.es.yml` (Spanish).
4. Commit your changes and run the deploy commands above to publish.

## Adding a New Translation

Follow these steps to add a new language, for example Portuguese (`pt`):

### 1. Create the docs directory

```
docs/pt/
├── stylesheets/
│   └── extra.css          # copy from docs/stylesheets/extra.css
├── index.md
├── installation.md
├── quickstart.md
├── auth.md
├── amounts.md
├── transport.md
├── webhooks.md
├── providers/
│   ├── index.md
│   ├── stripe.md
│   ├── paypal.md
│   ├── flow.md
│   ├── khipu.md
│   ├── generic.md
│   ├── dummy.md
│   └── custom.md
└── api-reference/
    ├── index.md
    ├── client.md
    ├── models.md
    ├── providers.md
    ├── auth.md
    ├── transport.md
    ├── amount.md
    └── webhooks.md
```

### 2. Create the mkdocs config file

Copy `mkdocs.es.yml` to `mkdocs.pt.yml` and update:

```yaml
site_description: "..."        # translated description
site_url: .../merchnts-cp/pt/
edit_uri: edit/main/docs/pt/
docs_dir: docs/pt
theme:
  language: pt                 # mkdocs-material language code
plugins:
  - search:
      lang: pt
```

### 3. Add the new language to the switcher

Add an entry to the `extra.alternate` list in **both** `mkdocs.yml` and `mkdocs.es.yml` (and all other language configs):

```yaml
extra:
  alternate:
    - name: English
      link: /merchnts-cp/
      lang: en
    - name: Español
      link: /merchnts-cp/es/
      lang: es
    - name: Português
      link: /merchnts-cp/pt/
      lang: pt
```

### 4. Translate the content

Translate all Markdown files in `docs/pt/`. Code blocks, `:::` API directives, and admonition types (`!!! tip`, `!!! warning`, etc.) should remain in English — only translate the surrounding prose and headings.

### 5. Build and preview

```bash
mkdocs serve -f mkdocs.pt.yml
```

### 6. Deploy

```bash
mkdocs gh-deploy -f mkdocs.pt.yml -d site/pt --remote-branch gh-pages
```

## Adding API Reference Pages

API reference pages use [`mkdocstrings`](https://mkdocstrings.github.io/) to auto-generate docs from Python docstrings. To add a new module to any language:

1. Create a new file in `docs/<lang>/api-reference/`, e.g. `docs/es/api-reference/mymodule.md`.
2. Add the `::: module.path` directive (same in all languages):

    ```markdown
    # Mi Módulo

    ::: merchants.mymodule.MyClass
    ```

3. Add an entry to the `nav` section in the corresponding `mkdocs.<lang>.yml`.

> **Note:** Docstrings are always rendered in their original language (English). Only the page title and surrounding prose need translation.

## Troubleshooting

**`mkdocs: command not found`**
Install with `pip install mkdocs mkdocs-material "mkdocstrings[python]"`.

**Import errors in API reference pages**
Make sure the package is installed in your current environment: `pip install -e .`

**Changes not reflected in the browser**
Hard-refresh the browser (`Ctrl+Shift+R` / `Cmd+Shift+R`) or restart `mkdocs serve`.

**Spanish deploy overwrites English**
Always deploy English first with `mkdocs gh-deploy`, then deploy other languages using `-d site/<lang>`.

## Alternative Tools — Zensical

[Zensical](https://zensical.org/) is a modern static site generator created by the same team behind
**Material for MkDocs**. It was analyzed as a potential replacement for the current MkDocs setup.

### Key findings (as of February 2026)

| Criterion | MkDocs + Material | Zensical |
|---|---|---|
| Maturity | Stable (≥ 1.6) | Alpha (0.0.23) |
| Config format | YAML (`mkdocs.yml`) | TOML (`zensical.toml`) |
| API reference via `mkdocstrings` | ✅ Supported | ❌ Not yet available |
| Multi-language support | ✅ Built-in | ✅ Built-in |
| Python ≥ 3.10 required | ✅ | ✅ |
| Plugin ecosystem | Mature | Early stage |

### Recommendation

**Stay with MkDocs + Material + mkdocstrings for now.**

The primary blocker is that Zensical does not yet offer a `mkdocstrings` equivalent.
This project relies on `mkdocstrings[python]` to auto-generate API reference pages directly
from Python docstrings (`:::` directives throughout `docs/api-reference/`).
Switching would break all API reference documentation until Zensical adds comparable plugin support.

Revisit this decision once Zensical reaches a stable release and provides a plugin for API
reference generation.
