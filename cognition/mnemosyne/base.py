from sqlalchemy.orm import declarative_base

# Shared Base for all Mnemosyne Stores
# Prevents multiple table registries and ensures schema consistency
Base = declarative_base()
