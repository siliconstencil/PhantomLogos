from cognition.mnemosyne.rational_store import Fact, MnemosyneRationalStore


def cleanup_facts():
    try:
        store = MnemosyneRationalStore()
        session = store.Session()

        # 1. Clear duplicates from facts table
        # We'll use SQLAlchemy to find and delete duplicates
        all_facts = session.query(Fact).all()
        seen = {}
        to_delete = []
        for f in all_facts:
            key = (f.subject, f.object)
            if key in seen:
                # Keep the one with higher confidence or more recent?
                # For now, just keep the first one seen (or the one with higher ID)
                old_f = seen[key]
                if f.id > old_f.id:
                    to_delete.append(old_f)
                    seen[key] = f
                else:
                    to_delete.append(f)
            else:
                seen[key] = f

        deleted_count = len(to_delete)
        for f in to_delete:
            session.delete(f)

        session.commit()
        session.close()

        # 2. Force WAL checkpoint and Vacuum via engine
        from sqlalchemy import text

        with store.engine.connect() as conn:
            conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
            # Vacuum cannot be run inside a transaction, but engines usually handle this
            # Actually, vacuum is best run via raw sqlite if needed

        print(f"Success: {deleted_count} duplicate facts deleted.")

    except Exception as e:
        print(f"Error during cleanup: {e}")


if __name__ == "__main__":
    cleanup_facts()
