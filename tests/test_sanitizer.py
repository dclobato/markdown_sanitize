from markdown_sanitize import sanitize_markdown_statement


def test_preserves_basic_formatting() -> None:
    md = "# Title\n\nPlain **bold** and *italic*.\n"
    result = sanitize_markdown_statement(md)
    assert result.markdown == "# Title\n\nPlain **bold** and *italic*.\n"
    assert result.changed is False
    assert result.removed_features == []


def test_preserves_lists_blockquotes_and_code_blocks() -> None:
    md = (
        "> quote\n\n"
        "- item 1\n"
        "- item 2\n\n"
        "```py\n"
        "print('https://example.com')\n"
        "<div>literal</div>\n"
        "```\n"
    )
    result = sanitize_markdown_statement(md)
    assert result.markdown == md
    assert result.changed is False


def test_inline_link_becomes_visible_text() -> None:
    result = sanitize_markdown_statement("See [docs](https://example.com) now.\n")
    assert result.markdown == "See docs now.\n"
    assert result.changed is True
    assert result.removed_features == ["link"]


def test_autolink_is_removed() -> None:
    result = sanitize_markdown_statement("Visit <https://example.com>.\n")
    assert result.markdown == "Visit .\n"
    assert result.changed is True
    assert result.removed_features == ["link"]


def test_images_are_removed_completely() -> None:
    result = sanitize_markdown_statement("Before ![alt](https://x/img.png) after\n")
    assert result.markdown == "Before  after\n"
    assert result.changed is True
    assert result.removed_features == ["image"]


def test_reference_links_and_definitions_are_removed() -> None:
    md = "Read [guide][ref].\n\n[ref]: https://example.com\n"
    result = sanitize_markdown_statement(md)
    assert result.markdown == "Read guide.\n"
    assert result.changed is True
    assert result.removed_features == ["link"]


def test_raw_html_is_removed() -> None:
    md = "<div>bad</div>\n\nA <a href='https://x'>link</a> here.\n"
    result = sanitize_markdown_statement(md)
    assert result.markdown == "A link here.\n"
    assert result.changed is True
    assert result.removed_features == ["html"]


def test_link_label_text_is_preserved() -> None:
    result = sanitize_markdown_statement("[important section](#section)\n")
    assert result.markdown == "important section\n"
    assert result.changed is True
    assert result.removed_features == ["link"]


def test_code_blocks_keep_url_like_or_html_like_text() -> None:
    md = "```\n<a href='https://x'>x</a>\nhttps://example.com\n```\n"
    result = sanitize_markdown_statement(md)
    assert result.markdown == md
    assert result.changed is False
    assert result.removed_features == []


def test_local_anchors_are_removed_but_text_remains() -> None:
    result = sanitize_markdown_statement("Go to [#secao](#secao)\n")
    assert result.markdown == "Go to #secao\n"
    assert result.changed is True
    assert result.removed_features == ["link"]


def test_output_is_stable_and_collapses_extra_blank_lines() -> None:
    md = "Line\n\n\n\n<div>x</div>\n\n\n[doc](https://x)\n"
    result = sanitize_markdown_statement(md)
    assert result.markdown == "Line\n\ndoc\n"
    assert result.changed is True
    assert result.removed_features == ["html", "link"]


def test_changed_is_true_when_markup_is_removed() -> None:
    result = sanitize_markdown_statement("<img src='https://x'>\n")
    assert result.markdown == "\n"
    assert result.changed is True
    assert result.removed_features == ["html"]
