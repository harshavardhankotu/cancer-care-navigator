"""Shared pytest setup: isolated temp DB BEFORE any app import."""

import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mkstemp(suffix='.db')[1]}"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
