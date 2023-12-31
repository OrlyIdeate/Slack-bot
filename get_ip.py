import socket
import pandas as pd
import mysql.connector
def get_local_ip():
    try:
        # ホスト名を取得し、それを使ってIPアドレスを取得
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    except Exception as e:
        return str(e)
# IPアドレスを取得して表示
print("Local IP Address:", get_local_ip())
config = {
    'user': 'root',
    'password': 'citson-buzrit-4cyxZu',
    'host': '35.223.243.48',
    'database': 'test1',
}
db_connection = mysql.connector.connect(**config)
cursor = db_connection.cursor()
# testテーブルのデータを取得
query = "SELECT * FROM phase4;"
df = pd.read_sql(query, con=db_connection)
# # 表にスタイルを適用する
# styled_df = df.style.set_properties(**{
#     'border-color': 'black',
#     'border-style': 'solid',
#     'border-width': '1px'
# }).set_table_styles([{
#     'selector': 'th',
#     'props': [('border-style', 'solid'),
#               ('border-width', '1px'),
#               ('border-color', 'black')]
# }])
# スタイルが適用された表を表示
print(df)
cursor.close()
db_connection.close()