import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine
from alembic import context
from alembic.script import ScriptDirectory

sys.path.append(os.getcwd())
from cognition.mnemosyne.models import MnemosyneBase, ReliabilityBase, SpatialBase

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _get_db_url(section_name: str) -> str:
    section = config.get_section(section_name) or {}
    return section.get("sqlalchemy.url", f"sqlite:///data/{section_name}.db")


DATABASES = {
    "mnemosyne": {"metadata": MnemosyneBase.metadata, "url": _get_db_url("mnemosyne")},
    "reliability": {"metadata": ReliabilityBase.metadata, "url": _get_db_url("reliability")},
    "spatial": {"metadata": SpatialBase.metadata, "url": _get_db_url("spatial")},
}

_BASE = os.path.dirname(__file__)


def run_migrations_online():
    section_name = config.config_ini_section
    
    if section_name == "alembic":
        print("Lutfen spesifik bir veritabani secin (Ornek: alembic -n mnemosyne upgrade head)")
        return

    conf = DATABASES.get(section_name)
    if not conf:
        print(f"Bilinmeyen section: {section_name}")
        return

    print(f"--- Running migrations for: {section_name} ---")
    connectable = create_engine(conf["url"])
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=conf["metadata"],
            version_table=f"alembic_version_{section_name}",
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    url = DATABASES["mnemosyne"]["url"]
    context.configure(url=url, target_metadata=DATABASES["mnemosyne"]["metadata"], literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()
