import os
import shutil

# 设置原始文件夹路径
source_folder = 'image'

# 创建目标文件夹路径
snapshot_folder = os.path.join(source_folder, 'snapshot')
halflength_folder = os.path.join(source_folder, 'halflength')

# 如果目标文件夹不存在，则创建
os.makedirs(snapshot_folder, exist_ok=True)
os.makedirs(halflength_folder, exist_ok=True)

# 遍历源文件夹中的文件
for filename in os.listdir(source_folder):
    # 获取文件的完整路径
    file_path = os.path.join(source_folder, filename)

    # 跳过文件夹
    if os.path.isdir(file_path):
        continue

    # 根据文件名判断文件类型并处理
    if 'snapshot' in filename:
        # 提取文件名中的前四个数字
        new_name = filename
        # 新文件的路径
        new_file_path = os.path.join(snapshot_folder, new_name)
    elif 'halflength' in filename:
        # 提取文件名中的前四个数字
        new_name = filename
        # 新文件的路径
        new_file_path = os.path.join(halflength_folder, new_name)
    else:
        # 如果文件名不包含'snapshot'或'halflength'，则跳过
        continue

    # 移动并重命名文件
    shutil.move(file_path, new_file_path)
    print(f'文件 {filename} 移动到 {new_file_path}')
