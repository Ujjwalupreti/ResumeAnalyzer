import logging
from contextlib import contextmanager
from mysql.connector import pooling
from config import settings

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class MySQLDatabase:
    """MySQL database wrapper with pooling and safe cursor management."""
    def __init__(self):
        try:
            self.connection_pool = pooling.MySQLConnectionPool(
                    pool_name="mypool",
                    pool_size=5,
                    host=settings.MYSQL_HOST,
                    port=settings.MYSQL_PORT,
                    user=settings.MYSQL_USER,
                    password=settings.MYSQL_PASSWORD,
                    database=settings.MYSQL_DATABASE,
                    charset='utf8mb4',          
                    use_unicode=True            
                )
            logger.info(f"MySQL connection pool created for DB '{settings.MYSQL_DB}'")
        except Exception as e:
            logger.critical(f"MySQL connection pool creation failed: {e}")
            raise

    def get_connection(self):
        return self.connection_pool.get_connection()

    @contextmanager
    def get_cursor(self, dictionary=True):
        conn = self.get_connection()
        cursor = conn.cursor(dictionary=dictionary)
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"MySQL transaction rolled back due to: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

    def execute_query(self, query, params=None):
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount

    def fetch_one(self, query, params=None):
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

    def fetch_all(self, query, params=None):
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()

mysql_db = MySQLDatabase()

def init_db():
    try:
        with mysql_db.get_cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchall()
        logger.info("✅ MySQL connection test successful.")
    except Exception as e:
        logger.error(f"❌ MySQL init failed: {e}")
        raise

def get_db():
    return mysql_db