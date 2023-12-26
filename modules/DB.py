import os
import mysql.connector

from dotenv import load_dotenv
load_dotenv()

# データベース接続設定を関数にまとめる
def get_db_config():
    return {
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASS'),
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
    }

# データベース接続を行う関数を作成
def connect_to_db():
    config = get_db_config()
    return mysql.connector.connect(**config)

# SQLクエリを実行し、結果を返す関数
def execute_query(query):
    """SQLクエリを実行し、結果を返します。

    引数:
        query (_type_): _description_

    戻り値:
        str: _description_
    """
    connection = connect_to_db()
    cursor = connection.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    connection.close()
    return result


