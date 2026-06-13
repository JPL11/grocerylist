"""
Shared pytest fixtures (optional challenge 4).

Runs against an in-memory SQLite database. A StaticPool keeps one connection
alive so the schema persists across session checkouts.
"""

import pytest
from sqlalchemy.pool import StaticPool

from app import create_app
from extensions import db


@pytest.fixture
def app_ctx():
    app = create_app(
        {
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "connect_args": {"check_same_thread": False},
                "poolclass": StaticPool,
            },
            "TESTING": True,
        }
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
