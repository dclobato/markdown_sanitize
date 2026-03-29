from __future__ import annotations

from markdown_sanitize import sanitize_markdown_statement


def main() -> None:
    raw_markdown = """
# Example Statement

This [external reference](https://example.com/docs) should lose the URL.

This [local section](#constraints) should also lose the anchor.

![architecture](https://example.com/diagram.png)

<div>unsafe html block</div>

> A quote with **formatting** remains.

- Item one
- Item two with `inline code`

```python
print("https://example.com is preserved inside code")
print("<div>HTML-looking text also stays in code</div>")
```
""".strip()

    result = sanitize_markdown_statement(raw_markdown)

    print("Raw markdown:")
    print(raw_markdown)
    print("\n" + "=" * 60 + "\n")

    print("Sanitized markdown:")
    print(result.markdown, end="")
    print("\n" + "=" * 60 + "\n")

    print(f"Changed: {result.changed}")
    print(f"Removed features: {result.removed_features}")


if __name__ == "__main__":
    main()
