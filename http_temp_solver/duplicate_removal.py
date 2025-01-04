import os
import shutil

# 定义文件夹路径
image_folder = 'image'
image_old_folder = 'image_old'

# 获取 image_old 文件夹下所有文件的路径
image_old_files = set()
for root, dirs, files in os.walk(image_old_folder):
    for file in files:
        image_old_files.add(os.path.relpath(os.path.join(root, file), image_old_folder))

# 遍历 image 文件夹，删除那些在 image_old 中存在的文件
for root, dirs, files in os.walk(image_folder):
    for file in files:
        file_rel_path = os.path.relpath(os.path.join(root, file), image_folder)
        if file_rel_path in image_old_files:
            file_path = os.path.join(root, file)
            print(f"Deleting: {file_path}")
            os.remove(file_path)  # 删除文件
            # 如果你想删除整个文件夹，可以使用 shutil.rmtree(file_path)
