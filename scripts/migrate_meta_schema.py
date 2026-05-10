import sqlite3
import os

def migrate_meta_schema():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, "data", "mnemosyne.db")
    
    print(f"Migrating mnemosyne.db (meta_cognition table)...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if session_id exists
        cursor.execute("PRAGMA table_info(meta_cognition)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "session_id" not in columns:
            print("  Adding 'session_id' column to meta_cognition...")
            cursor.execute("ALTER TABLE meta_cognition ADD COLUMN session_id TEXT DEFAULT ''")
            conn.commit()
            print("  [SUCCESS] Column added.")
        else:
            print("  [SKIP] 'session_id' column already exists.")
            
    except Exception as e:
        print(f"  [ERROR] Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_meta_schema()
