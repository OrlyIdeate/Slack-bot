import os
import mysql.connector

from dotenv import load_dotenv
load_dotenv()


def get_db_config():
    """
    データベース接続設定
    """
    return {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASS'),
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
    }

def connect_to_db():
    """
    データベース接続
    """
    config = get_db_config()
    return mysql.connector.connect(**config)

def execute_query(query):
    """SQLクエリを実行し、結果を返します。

    引数:
        query : str型のSQLクエリ

    戻り値:
        result: list型の結果
    """
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    connection.close()
    return result


