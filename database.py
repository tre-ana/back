HOST = "localhost"
PORT = 3306
USERNAME = "root"
PASSWORD = "1234"
DBNAME = "treana"

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker

DB_URL = f'mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}'

class engineconn:

    def __init__(self):
        self.engine = create_engine(DB_URL, pool_recycle = 500)

    def sessionmaker(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        return session

    def connection(self):
        conn = self.engine.connect()
        return conn