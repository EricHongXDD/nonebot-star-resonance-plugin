from .request_client import RequestClient
import asyncio
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
base_path = os.path.dirname(os.path.abspath(__file__))  # 获取当前文件的绝对路径
image_path = os.path.join(base_path, 'image', 'relation_model.png')


def get_default_avatar(default_avatar_path: str):
    """
    获取默认头像。
    :param default_avatar_path: 默认头像文件路径。
    """
    try:
        with open(default_avatar_path, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        print(f"默认头像文件未找到: {default_avatar_path}")
        return b""


class Service(object):
    def __init__(self):
        self.qlogo_request = RequestClient('q4.qlogo.cn')

    def download_avatar(self, user_id: str, size: int):
        """
        下载 QQ 用户头像并保存到本地。
        :param user_id: QQ 用户 ID。
        :param size: 头像尺寸(支持140,640)。
        """
        endpoint = 'https://q4.qlogo.cn'
        api = '/g'
        method = 'GET'
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
        params = {
            'b': 'qq',
            'nk': str(user_id),
            's': str(size)
        }

        default_avatar_path = os.path.join(base_path, 'image', 'default_avatar.jpg')

        try:
            resp, content = self.qlogo_request.sendRequest(api, method, params=params, body=None, headers=headers)
            status_code = resp.get("status")

            if status_code == '200':
                return content
            else:
                print(f"请求失败，状态码: {status_code}, 使用默认头像。")
                return get_default_avatar(default_avatar_path)

        except Exception as e:
            print(f"下载图片时发生错误: {e}, 使用默认头像。")
            return get_default_avatar(default_avatar_path)

    async def process_image(self, image_files_data, text, font_path=os.path.join(base_path, 'font', 'Alibaba-PuHuiTi-Medium.ttf'), font_size=50):
        """
        处理图像并添加竖排文字，返回最终图像的二进制数据。

        :param image_files_data: 包含a.png~h.png的二进制数据的列表，顺序为a.png, b.png, c.png, d.png, e.png, f.png, g.png, h.png
        :param text: 要添加的竖排文字
        :param font_path: 字体文件路径，默认是'Alibaba-PuHuiTi-Medium.ttf'
        :param font_size: 初始字体大小，默认是50
        :return: 图像的二进制数据
        """
        # 打开背景
        background = Image.open(os.path.join(base_path, 'image', 'relation_model.png'))

        # 8个方块的位置 (左上角和右下角坐标)
        positions = [
            ((558, 83), (842, 367)),  # 第1个方块
            ((991, 83), (1275, 366)),  # 第2个方块
            ((125, 588), (409, 871)),  # 第3个方块
            ((558, 588), (842, 871)),  # 第4个方块
            ((991, 588), (1275, 871)),  # 第5个方块
            ((1424, 588), (1708, 871)),  # 第6个方块
            ((342, 1093), (625, 1376)),  # 第7个方块
            ((1208, 1093), (1492, 1376))  # 第8个方块
        ]

        # 处理每一个a~h.png图像
        for i, image_data in enumerate(image_files_data):
            img = Image.open(BytesIO(image_data))  # 读取二进制数据为图像

            # 计算目标区域的宽度和高度
            left_top, right_bottom = positions[i]
            width = right_bottom[0] - left_top[0]
            height = right_bottom[1] - left_top[1]

            # 调整图像大小为目标区域大小
            img_resized = img.resize((width, height))

            # 将调整后的图像粘贴到背景图上
            background.paste(img_resized, left_top)

        # 创建一个ImageDraw对象
        draw = ImageDraw.Draw(background)

        # 计算给定区域的高度
        text_left = 479
        text_top = 11
        text_right = 546
        text_bottom = 435
        area_height = text_bottom - text_top

        # 先加载字体，计算每个字符的大小
        font = ImageFont.truetype(font_path, font_size)

        # 获取第一个字符的边界框
        bbox = draw.textbbox((0, 0), text[0], font=font)  # 以第一个字符为例
        char_width = bbox[2] - bbox[0]  # 计算字符的宽度
        char_height = bbox[3] - bbox[1]  # 计算字符的高度

        # 计算竖排文字的总高度
        total_height = len(text) * char_height  # 竖排文字的总高度

        # 如果竖排文字的总高度超出区域高度，调整字体大小
        while total_height > area_height:
            font_size -= 1  # 减小字体大小
            if font_size < 10:  # 防止字体过小
                break
            font = ImageFont.truetype(font_path, font_size)  # 更新字体大小
            bbox = draw.textbbox((0, 0), text[0], font=font)
            char_height = bbox[3] - bbox[1]  # 更新字符高度
            total_height = len(text) * char_height  # 更新总高度

        # 计算竖排文字的起始位置，水平居中，垂直居中
        text_x = (text_right + text_left - char_width) // 2  # 水平居中
        text_y_start = (text_bottom + text_top - total_height) // 2  # 垂直居中

        # 绘制竖排文字，每个字符垂直排列
        for i, char in enumerate(text):
            text_y = text_y_start + i * char_height  # 每个字符之间的垂直间距
            draw.text((text_x, text_y), char, font=font, fill=(255, 255, 255))  # 白色文字

        # 使用BytesIO保存最终图像并返回二进制数据
        output_image = BytesIO()
        background.save(output_image, format='PNG')
        output_image.seek(0)  # 将指针移到开头

        # 返回二进制图像数据
        return output_image.read()


# s = Service()
# avatar = s.download_avatar('1025', 140)
#
# image_files_data = []
# image_files_data.append(avatar)
# for i in range(7):
#     image_files_data.append(avatar)
#     # with open(f'image/{chr(97 + i)}.png', 'rb') as f:
#     #     image_files_data.append(f.read())
# text = "test"
#
#
# async def start():
#     result_image_data = await s.process_image(image_files_data, text)
#     # 将 `result_image_data` 传递给其他函数，或直接保存到文件
#     with open('output_with_vertical_text_resized.png', 'wb') as f:
#         f.write(result_image_data)
#
#
# asyncio.run(start())
