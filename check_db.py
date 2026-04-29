import sqlite3

def run():
    conn = sqlite3.connect("glucoguide_final_v1.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(medical_profiles);")
    columns = cursor.fetchall()
    print("Columns in medical_profiles:")
    for col in columns:
        print(f" - {col[1]} ({col[2]})")

    conn.close()

if __name__ == "__main__":
    run()
