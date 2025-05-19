import sqlite3

def init_db(db_path='finance.db', sql_path='sql/create_tables.sql'):
    # 連接 SQLite（會自動建立檔案）
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 讀取 SQL 檔案並執行
    with open(sql_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    cursor.executescript(sql_script)

    conn.commit()
    conn.close()
    print(f"✅ 資料庫 '{db_path}' 建立成功。")

if __name__ == "__main__":
    init_db()
