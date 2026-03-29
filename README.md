# markdown_sanitize

`markdown_sanitize` is a Python package for sanitizing Markdown statements before storage and later rendering.

It keeps a safe Markdown subset and removes features that should not survive in problem statements, including:

- inline links
- reference links
- autolinks
- local anchors
- images
- raw HTML
- link and image reference definitions

The output remains Markdown, not HTML.

## Installation

From PyPI:

```bash
pip install markdown_sanitize
```

For local development with `uv`:

```bash
uv sync --group dev
```

## What It Preserves

The sanitizer preserves:

- paragraphs
- headings
- bold and italic
- blockquotes
- ordered and unordered lists
- inline code
- fenced code blocks
- horizontal rules
- line breaks

## Basic Usage

```python
from markdown_sanitize import sanitize_markdown_statement

raw_markdown = """
# Example

See [the docs](https://example.com/docs).

![diagram](https://example.com/diagram.png)

<div>unsafe html</div>

```python
print("https://example.com stays inside code")
```
"""

result = sanitize_markdown_statement(raw_markdown)

print(result.markdown)
print(result.changed)
print(result.removed_features)
```

Expected output:

```text
# Example

See the docs.

```python
print("https://example.com stays inside code")
```
```

And:

```text
True
['html', 'image', 'link']
```

## Result Object

`sanitize_markdown_statement()` returns `SanitizedMarkdownResult`:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SanitizedMarkdownResult:
    markdown: str
    changed: bool
    removed_features: list[str]
```

Fields:

- `markdown`: sanitized Markdown ready to store
- `changed`: `True` when content was removed or normalized
- `removed_features`: predictable categories such as `link`, `image`, and `html`

## Example Script

A runnable example is available at [`examples/sample.py`](/home/dclobato/markdown_cleanup/examples/sample.py).

Run it locally with:

```bash
uv run python examples/sample.py
```

## Development

Install development dependencies:

```bash
uv sync --group dev
```

Run the checks:

```bash
uv run pytest -q
uv run ruff check .
uv run mypy src
```
