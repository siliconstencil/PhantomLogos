from sqlalchemy import create_engine

from cognition.mnemosyne.meta_cognition import Base, ReliabilityBase
from src.utils.project_path import to_absolute_path


def create():
    db_path = to_absolute_path("data/reliability.db")
    engine = create_engine(f"sqlite:///{db_path}")
    print(f"Creating tables in {db_path}...")
    Base.metadata.create_all(engine)
    ReliabilityBase.metadata.create_all(engine)
    print("Done.")


if __name__ == "__main__":
    create()
