"""add_reflection_entity_failure_tables (NO-OP marker)

All 4 tables (entities, reflections, semantic_relations, failure_memory)
already exist in the DB via raw sqlite3 CREATE TABLE IF NOT EXISTS.
This migration marks them under Alembic version control without schema changes.
SQLite loose typing makes all TEXT <-> String() type changes no-ops.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "594e9f875cb2"
down_revision: Union[str, Sequence[str], None] = "4f4418aa5ad9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """No-op. Tables already exist. SQLite ignores TEXT <-> String() type changes."""
    pass


def downgrade() -> None:
    """No-op. Revert would require dropping 4 tables — not done automatically."""
    pass
