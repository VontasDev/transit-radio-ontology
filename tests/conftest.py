"""Shared pytest fixtures and path helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"
SCHEMAS_DIR = REPO_ROOT / "schemas"


def _example_files():
    return sorted(EXAMPLES_DIR.glob("*.json"))


@pytest.fixture(params=_example_files(), ids=lambda p: p.name)
def example_file(request) -> Path:
    return request.param


@pytest.fixture
def examples_dir() -> Path:
    return EXAMPLES_DIR


@pytest.fixture
def schemas_dir() -> Path:
    return SCHEMAS_DIR
