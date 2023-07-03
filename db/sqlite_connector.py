import sqlite3


class SQLiteConnector:
    def __init__(self, db_path):
        self.db_path = db_path
        self._conn = None
        self._cursor = None

    @property
    def conn(self):
        if not self._conn:
            self._conn = sqlite3.connect(self.db_path)
        return self._conn

    @property
    def cursor(self):
        if not self._cursor:
            self._cursor = self.conn.cursor()
        return self._cursor

    def execute(self, *args):
        try:
            self.cursor.execute(*args)
            self.conn.commit()
        except Exception as e:
            print(f'Error during database command execution - {e}')

    def db_teardown(self):
        self.cursor.close()
        self.conn.close()


class SensorsDataDbHandler(SQLiteConnector):

    def __init__(self, db_path):
        super().__init__(db_path)
        self.dht_table = 'dht_data'
        self.mq2_table = 'mq2_data'

    def init_dht_table(self):
        self.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {self.dht_table}
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                temperature REAL,
                humidity REAL
            )
            '''
        )

    def init_mq2_table(self):
        self.execute(
            f'''
            CREATE TABLE IF NOT EXISTS {self.mq2_table}
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                lpg REAL,
                co REAL,
                smoke REAL,
                propane REAL,
                hydrogen REAL,
                alcohol REAL,
                methane REAL
            )
            '''
        )

    def insert_dht_data(self, date, temp, humidity):
        self.execute(
            f"INSERT INTO {self.dht_table} (date, temperature, humidity) "
            "VALUES (?, ?, ?)",
            (date, temp, humidity)
        )

    def insert_mq2_data(self, date, mq_data):
        self.execute(
            f"INSERT INTO {self.mq2_table} (date, lpg, co, smoke, propane, hydrogen, alcohol, methane)"
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (date, *mq_data)
        )


