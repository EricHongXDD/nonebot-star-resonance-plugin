import os
import mysql.connector
from PIL import Image
import io
from mysql.connector import Error


# MySQL 数据库连接参数
db_config = {
    'user': '',
    'password': '',
    'host': '',
    'port': '',
    'database': ''
}


# 连接到 MySQL 数据库
def connect_to_db():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("成功连接到数据库")
            return connection
    except Error as e:
        print(f"数据库连接失败: {e}")
        return None


def store_images_to_db(table_name, folder_path):
    conn = connect_to_db()
    cursor = conn.cursor()

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # 检查文件是否是图片（可以根据扩展名进行检查）
        if os.path.isfile(file_path) and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            try:
                # 打开图片并转换为二进制数据
                with open(file_path, 'rb') as file:
                    image_data = file.read()

                # 注意改动
                str_data = 'halflength'
                image_name = filename.split(str_data)[0] + str_data
                image_id = filename.split(str_data)[1].split('.')[0]
                # 插入图片数据到数据库
                cursor.execute(f"INSERT INTO {table_name} (image_name, image_id, image_data) VALUES (%s, %s, %s)",
                               (image_name, image_id, image_data))
                conn.commit()
                print(f"成功插入 {image_name} 到数据库")

            except Exception as e:
                print(f"无法处理文件 {filename}: {e}")
                continue

    # 提交事务并关闭连接
    cursor.close()
    conn.close()
    print("所有图片已成功存储到数据库。")


def store_images_to_db_batch(table_name, folder_path):
    conn = connect_to_db()
    cursor = conn.cursor()

    insert_data = []  # 用于批量插入的列表

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # 检查文件是否是图片
        if os.path.isfile(file_path) and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            try:
                # 打开图片并转换为二进制数据
                with open(file_path, 'rb') as file:
                    image_data = file.read()
                    # 注意改动
                    image_name = filename.split('snapshot')[0] + 'snapshot'
                    image_id = filename.split('snapshot')[1].split('.')[0]
                # 将文件名和二进制数据添加到插入列表
                insert_data.append((image_name, image_id, image_data))

            except Exception as e:
                print(f"无法处理文件 {image_name}: {e}")
                continue

    # 批量插入数据
    if insert_data:
        cursor.executemany(f"INSERT INTO {table_name} (image_name, image_id, image_data) VALUES (%s, %s, %s)", insert_data)
        conn.commit()

    # 关闭连接
    cursor.close()
    conn.close()
    print(f"{len(insert_data)} 张图片已成功存储到数据库。")


# 调用批量插入函数
store_images_to_db('halflengthV2', 'image/halflength')
