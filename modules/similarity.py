import os
import numpy as np
import pandas as pd
import openai
import mysql.connector
import pickle

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text):
    response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
    )
    # 応答から埋め込みデータを取得する正しい方法を使用
    embedding = response.data[0].embedding
    return embedding


# コサイン類似度計算式
def cosine_similarity(vec_a, vec_b):
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    return dot_product / (norm_a * norm_b)



def get_top_5_similar_texts(message_text):
    vector1 = get_embedding(message_text)
    config = {
        'user': 'root',
        'password': 'citson-buzrit-4cyxZu',
        'host': '35.223.243.48',
        'database': 'test1',
        }
    db_connection = mysql.connector.connect(**config)
    cursor = db_connection.cursor()
    query = "SELECT content, vector, url, date, category FROM phese4;"
    cursor.execute(query)
    rows = cursor.fetchall()
    similarity_list = []
    for content, vector_bytes, url, date, category in rows:
        vector2 = pickle.loads(vector_bytes)
        similarity = cosine_similarity(vector1, vector2)
        similarity_list.append((similarity, content, url, date, category))
    similarity_list.sort(reverse=True)
    return similarity_list[:5]