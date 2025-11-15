#!/usr/bin/env python3
"""Initialize Chainlit database tables."""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))


def init_database():
    """Initialize database tables using SQLAlchemy."""
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)

    db_path = data_dir / "chainlit.db"
    print(f"Initializing database at {db_path}...")

    try:
        from sqlalchemy import (
            Column,
            Integer,
            MetaData,
            String,
            Table,
            Text,
            create_engine,
        )

        conninfo = f"sqlite:///{db_path}"
        engine = create_engine(conninfo, echo=False)
        metadata = MetaData()

        # Define Chainlit tables schema based on Chainlit's data layer
        users_table = Table(
            'users',
            metadata,
            Column('id', String, primary_key=True),
            Column('identifier', String, nullable=False, unique=True),
            Column('createdAt', String),
            Column('metadata', Text),
        )

        # Threads table
        threads_table = Table(
            'threads',
            metadata,
            Column('id', String, primary_key=True),
            Column('createdAt', String),
            Column('name', String),
            Column('userId', String),
            Column('userIdentifier', String),
            Column('tags', Text),
            Column('metadata', Text),
        )

        # Steps table
        steps_table = Table(
            'steps',
            metadata,
            Column('id', String, primary_key=True),
            Column('name', String, nullable=False),
            Column('type', String, nullable=False),
            Column('threadId', String, nullable=False),
            Column('parentId', String),
            Column('streaming', Integer),
            Column('waitForAnswer', Integer),
            Column('isError', Integer),
            Column('metadata', Text),
            Column('tags', Text),
            Column('input', Text),
            Column('output', Text),
            Column('createdAt', String),
            Column('start', String),
            Column('end', String),
            Column('generation', Text),
            Column('showInput', String),
            Column('defaultOpen', Integer),
            Column('language', String),
            Column('indent', Integer),
        )

        # Elements table
        elements_table = Table(
            'elements',
            metadata,
            Column('id', String, primary_key=True),
            Column('threadId', String),
            Column('type', String),
            Column('url', String),
            Column('chainlitKey', String),
            Column('name', String, nullable=False),
            Column('display', String),
            Column('objectKey', String),
            Column('size', String),
            Column('page', Integer),
            Column('language', String),
            Column('forId', String),
            Column('mime', String),
            Column('props', Text),
        )

        # Feedbacks table
        feedbacks_table = Table(
            'feedbacks',
            metadata,
            Column('id', String, primary_key=True),
            Column('forId', String, nullable=False),
            Column('threadId', String, nullable=False),
            Column('value', Integer, nullable=False),
            Column('comment', String),
        )

        # Create all tables
        metadata.create_all(engine)

        # Verify tables were created and add missing columns
        import sqlite3

        def ensure_column(conn, table, column, sql_type):
            """Add column to table if missing."""
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table});")
            existing = {col[1] for col in cursor.fetchall()}
            if column not in existing:
                print(f"Adding missing '{column}' column to {table} table...")
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type};")
                conn.commit()
                print(f"✓ Added '{column}' column to {table} table")

        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        try:
            ensure_column(conn, "elements", "props", "TEXT")
        except Exception as e:
            print(f"⚠ Warning: Could not add props column: {e}")

        try:
            ensure_column(conn, "steps", "defaultOpen", "INTEGER")
        except Exception as e:
            print(f"⚠ Warning: Could not add defaultOpen column: {e}")

        conn.close()

        if tables:
            print(f"✓ Created tables: {[t[0] for t in tables]}")
        else:
            print("⚠ Warning: No tables found after initialization")
            sys.exit(1)

        engine.dispose()
        print("✓ Database initialization completed successfully")

    except Exception as e:
        import traceback
        print(f"✗ Error initializing database: {e}")
        print(f"  Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()

