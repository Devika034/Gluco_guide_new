import sqlite3
import traceback

def main():
    db_path = "glucoguide_final_v1.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    columns_to_add = [
        ("uacr", "FLOAT"),
        ("egfr", "FLOAT")
    ]

    for col_name, col_type in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE medical_profiles ADD COLUMN {col_name} {col_type};")
            print(f"Successfully added column '{col_name}' to medical_profiles")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column '{col_name}' already exists.")
            else:
                print(f"Error adding column '{col_name}': {e}")
                traceback.print_exc()
        except Exception as e:
            print(f"Unexpected error adding column '{col_name}': {e}")
            traceback.print_exc()

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
