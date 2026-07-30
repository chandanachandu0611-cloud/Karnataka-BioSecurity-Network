import glob
import sqlite3

db_files = glob.glob("**/*.db", recursive=True)

if not db_files:
    print("No database file found!")
else:
    for db_path in db_files:
        print(f"Updating database file: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("ALTER TABLE incidents ADD COLUMN voice_url TEXT")
            print("-> Successfully added voice_url column")
        except Exception as e:
            print(f"-> voice_url check: {e}")

        try:
            cursor.execute(
                "ALTER TABLE incidents ADD COLUMN voice_transcription TEXT"
            )
            print("-> Successfully added voice_transcription column")
        except Exception as e:
            print(f"-> voice_transcription check: {e}")

        conn.commit()
        conn.close()

    print("\nDatabase update complete!")