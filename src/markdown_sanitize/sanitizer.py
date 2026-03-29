from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from markdown_it import MarkdownIt
from markdown_it.token import Token


_REFERENCE_DEFINITION_PREFIXES = ("[", "![")


@dataclass(frozen=True)
class SanitizedMarkdownResult:
    markdown: str
    changed: bool
    removed_features: list[str]


def sanitize_markdown_statement(md_text: str) -> SanitizedMarkdownResult:
    parser = MarkdownIt("commonmark", {"html": True})
    tokens = parser.parse(md_text)

    removed_features: set[str] = set()
    pieces: list[str] = []

    index = 0
    while index < len(tokens):
        rendered, consumed = _render_block(tokens, index, removed_features)
        if rendered:
            pieces.append(rendered)
        index += consumed

    markdown = _normalize_markdown("".join(pieces))

    if _contains_reference_definition(md_text):
        removed_features.add("link")

    changed = markdown != _normalize_markdown(md_text)
    return SanitizedMarkdownResult(
        markdown=markdown,
        changed=changed,
        removed_features=sorted(removed_features),
    )


def _render_block(
    tokens: list[Token], start: int, removed_features: set[str]
) -> tuple[str, int]:
    token = tokens[start]

    if token.type in {"html_block"}:
        removed_features.add("html")
        return "", 1

    if token.type in {"paragraph_open", "heading_open", "blockquote_open", "bullet_list_open", "ordered_list_open", "list_item_open"}:
        end = _find_matching_close(tokens, start)
        body = tokens[start + 1 : end]

        if token.type == "paragraph_open":
            return _render_paragraph(body, removed_features), end - start + 1
        if token.type == "heading_open":
            return _render_heading(token, body, removed_features), end - start + 1
        if token.type == "blockquote_open":
            return _render_blockquote(body, removed_features), end - start + 1
        if token.type in {"bullet_list_open", "ordered_list_open"}:
            return _render_list(token, body, removed_features), end - start + 1
        if token.type == "list_item_open":
            return _render_list_item(body, removed_features), end - start + 1

    if token.type == "fence":
        info = token.info.strip()
        opener = f"```{info}".rstrip()
        content = token.content
        if not content.endswith("\n"):
            content += "\n"
        return f"{opener}\n{content}```\n\n", 1

    if token.type == "code_block":
        content = token.content
        if not content.endswith("\n"):
            content += "\n"
        return f"```\n{content}```\n\n", 1

    if token.type == "hr":
        return "---\n\n", 1

    if token.type == "inline":
        text = _render_inline(token.children or [], removed_features).strip()
        return (f"{text}\n\n" if text else ""), 1

    return "", 1


def _render_paragraph(children: list[Token], removed_features: set[str]) -> str:
    text = _render_blocks(children, removed_features).strip()
    return f"{text}\n\n" if text else ""


def _render_heading(open_token: Token, children: list[Token], removed_features: set[str]) -> str:
    level = int(open_token.tag[1]) if len(open_token.tag) == 2 and open_token.tag.startswith("h") else 1
    text = _render_blocks(children, removed_features).strip()
    return f"{'#' * max(1, min(level, 6))} {text}\n\n" if text else ""


def _render_blockquote(children: list[Token], removed_features: set[str]) -> str:
    inner = _normalize_markdown(_render_blocks(children, removed_features))
    if not inner:
        return ""
    quoted = "\n".join(
        ">"
        if not line.strip()
        else f"> {line}"
        for line in inner.rstrip("\n").split("\n")
    )
    return f"{quoted}\n\n"


def _render_list(open_token: Token, children: list[Token], removed_features: set[str]) -> str:
    items = _collect_list_items(children)
    if not items:
        return ""

    ordered = open_token.type == "ordered_list_open"
    start = int(open_token.attrGet("start") or 1) if ordered else 1
    rendered_items: list[str] = []

    for idx, item_tokens in enumerate(items):
        marker = f"{start + idx}." if ordered else "-"
        rendered_item = _render_list_item(item_tokens, removed_features)
        if rendered_item:
            rendered_items.append(_prefix_list_item(marker, rendered_item))

    return "".join(rendered_items) + ("\n" if rendered_items else "")


def _render_list_item(children: list[Token], removed_features: set[str]) -> str:
    content = _render_blocks(children, removed_features).rstrip("\n")
    return content


def _render_blocks(tokens: list[Token], removed_features: set[str]) -> str:
    pieces: list[str] = []
    index = 0
    while index < len(tokens):
        rendered, consumed = _render_block(tokens, index, removed_features)
        if rendered:
            pieces.append(rendered)
        index += consumed
    return "".join(pieces)


def _render_inline(tokens: Iterable[Token], removed_features: set[str]) -> str:
    pieces: list[str] = []
    tokens = list(tokens)
    index = 0

    while index < len(tokens):
        token = tokens[index]

        if token.type == "text":
            pieces.append(token.content)
            index += 1
            continue

        if token.type == "softbreak":
            pieces.append("\n")
            index += 1
            continue

        if token.type == "hardbreak":
            pieces.append("  \n")
            index += 1
            continue

        if token.type == "code_inline":
            pieces.append(f"`{token.content}`")
            index += 1
            continue

        if token.type in {"em_open", "strong_open"}:
            end = _find_matching_close_inline(tokens, index)
            marker = "*" if token.type == "em_open" else "**"
            inner = _render_inline(tokens[index + 1 : end], removed_features)
            pieces.append(f"{marker}{inner}{marker}")
            index = end + 1
            continue

        if token.type == "link_open":
            removed_features.add("link")
            end = _find_matching_close_inline(tokens, index)
            if _is_autolink(token):
                index = end + 1
                continue
            inner = _render_inline(tokens[index + 1 : end], removed_features)
            pieces.append(inner)
            index = end + 1
            continue

        if token.type == "image":
            removed_features.add("image")
            index += 1
            continue

        if token.type == "html_inline":
            removed_features.add("html")
            index += 1
            continue

        if token.type == "inline":
            pieces.append(_render_inline(token.children or [], removed_features))
            index += 1
            continue

        index += 1

    return "".join(pieces)


def _find_matching_close(tokens: list[Token], start: int) -> int:
    level = 0
    for idx in range(start, len(tokens)):
        token = tokens[idx]
        if token.nesting == 1:
            level += 1
        elif token.nesting == -1:
            level -= 1
            if level == 0:
                return idx
    raise ValueError(f"Unmatched block token {tokens[start].type}")


def _find_matching_close_inline(tokens: list[Token], start: int) -> int:
    open_type = tokens[start].type
    close_type = open_type.replace("_open", "_close")
    level = 0
    for idx in range(start, len(tokens)):
        token = tokens[idx]
        if token.type == open_type:
            level += 1
        elif token.type == close_type:
            level -= 1
            if level == 0:
                return idx
    raise ValueError(f"Unmatched inline token {open_type}")


def _collect_list_items(tokens: list[Token]) -> list[list[Token]]:
    items: list[list[Token]] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.type != "list_item_open":
            index += 1
            continue
        end = _find_matching_close(tokens, index)
        items.append(tokens[index + 1 : end])
        index = end + 1
    return items


def _prefix_list_item(marker: str, body: str) -> str:
    lines = body.splitlines()
    if not lines:
        return ""
    prefixed = [f"{marker} {lines[0]}"]
    for line in lines[1:]:
        prefixed.append("  " + line if line else "")
    return "\n".join(prefixed) + "\n"


def _normalize_markdown(markdown: str) -> str:
    lines = [line.rstrip() for line in markdown.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    collapsed: list[str] = []
    blank_count = 0

    for line in lines:
        if line.strip():
            blank_count = 0
            collapsed.append(line)
            continue

        blank_count += 1
        if blank_count <= 1:
            collapsed.append("")

    while collapsed and not collapsed[0]:
        collapsed.pop(0)
    while collapsed and not collapsed[-1]:
        collapsed.pop()

    normalized = "\n".join(collapsed)
    return f"{normalized}\n" if normalized else "\n"


def _contains_reference_definition(md_text: str) -> bool:
    for raw_line in md_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.lstrip()
        if not line.startswith(_REFERENCE_DEFINITION_PREFIXES):
            continue
        if "]:" not in line:
            continue
        return True
    return False


def _is_autolink(token: Token) -> bool:
    return token.markup == "autolink" or token.info == "auto"
