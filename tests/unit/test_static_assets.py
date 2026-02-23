"""Tests for static CSS asset validity."""

import pathlib

import pytest
import tinycss2

CSS_DIR = pathlib.Path(__file__).parent.parent.parent / "datasette" / "static"


@pytest.mark.parametrize(
    "css_file",
    sorted(CSS_DIR.glob("*.css")),
    ids=lambda p: p.name,
)
def test_css_parses_without_errors(css_file):
    """CSS file must parse without tinycss2 ParseError nodes."""
    rules, _ = tinycss2.parse_stylesheet_bytes(css_file.read_bytes())
    errors = [node for node in rules if node.type == "error"]
    assert errors == [], f"Parse errors in {css_file.name}: {errors}"
