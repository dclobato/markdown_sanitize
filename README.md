# markdown_sanitize

`markdown_sanitize` is a Python package for sanitizing Markdown statements before storage and later rendering.

## Breaking Change in 2.0.0

Version `2.0.0` adds the `reformatted: bool` field to `SanitizedMarkdownResult`.

If your code instantiates `SanitizedMarkdownResult` directly, unpacks it, or depends on the previous public result shape, update it to handle the new field.

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
uv sync --extra dev
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
print(result.reformatted)
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
False
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
    reformatted: bool
    removed_features: list[str]
```

Fields:

- `markdown`: sanitized Markdown ready to store
- `changed`: `True` when the output Markdown differs textually from the input
- `reformatted`: `True` when the sanitizer only normalized formatting or whitespace, without removing disallowed features
- `removed_features`: predictable categories such as `link`, `image`, and `html`

Typical interpretations:

- `changed=False`, `reformatted=False`, `removed_features=[]`: input already matched the sanitized form
- `changed=True`, `reformatted=True`, `removed_features=[]`: only formatting changed
- `changed=True`, `reformatted=False`, `removed_features!=[]`: disallowed content was removed

## Example Script

A runnable example is available at [`examples/sample.py`](examples/sample.py).

Run it locally with:

```bash
uv run python examples/sample.py
```

## Development

Install development dependencies:

```bash
uv sync --extra dev
```

Run the checks:

```bash
uv run pytest -q
uv run ruff check .
uv run mypy src
```
