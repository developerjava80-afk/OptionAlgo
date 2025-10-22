import pandas as pd
import pymysql
from sqlalchemy import create_engine, text

class DBConnector:
    def __init__(self, config):
        self.config = config
        self.engine = create_engine(
            f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}/{config['database']}"
        )

    def get_tables(self):
        with self.engine.connect() as conn:
            tables = conn.execute(text("SHOW TABLES")).fetchall()
            if not tables:
                raise Exception("No tables found in the database.")
            table_names = [t[0] for t in tables]
            dfs = [pd.read_sql(f"SELECT * FROM `{name}`", conn) for name in table_names]
        return dfs, table_names
