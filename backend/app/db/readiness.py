from sqlalchemy import text

from backend.app.db.session import engine


def wait_for_database() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))