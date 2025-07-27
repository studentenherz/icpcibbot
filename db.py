import sqlite3


class DBHandler:
    def __init__(self, database_name: str):
        self._db_con = sqlite3.connect(database_name)
        self._cur = self._db_con.cursor()
        self._init_tables()

    def _init_tables(self):
        self._cur.execute("CREATE TABLE IF NOT EXISTS tags (name TEXT UNIQUE NOT NULL)")
        self._db_con.commit()

    def get_tags(self) -> list[str]:
        res = self._cur.execute("SELECT name FROM tags")
        return [row[0] for row in res.fetchall()]

    def insert_tag(self, new_tag: str) -> bool:
        try:
            self._cur.execute("INSERT INTO tags VALUES (?)", (new_tag,))
            self._db_con.commit()
            return True
        except Exception as e:
            print(e)
            return False
