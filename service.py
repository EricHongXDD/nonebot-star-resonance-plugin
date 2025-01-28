import hashlib
import json
import time
import uuid
import mimetypes
from codecs import encode
from .request_client import RequestClient, CffiClient
import asyncio
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os
from . import headers
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
        self.headers = headers
        self.qlogo_request = RequestClient('q4.qlogo.cn')
        self.kl_request = RequestClient('klingai.kuaishou.com')
        self.kuaishouzt_request = RequestClient('upload.kuaishouzt.com')
        self.viggle_request = CffiClient('www.viggle.ai')
        self.vigglecdn_request = RequestClient('cdn.viggle.ai')
        # 打开文件并读取内容
        cookies_path = os.path.join(base_path, 'cookies')
        kl_01_cookies = os.path.join(cookies_path, 'kl_01.cookies')
        viggle_01_key = os.path.join(cookies_path, 'viggle_01.key')
        with open(kl_01_cookies, 'r') as file:
            self.kl_cookies = file.read()
        with open(viggle_01_key, 'r') as file:
            self.viggle_key = file.read()

    def download_avatar(self, user_id: str, size: int):
        """
        下载 QQ 用户头像并保存到本地。
        :param user_id: QQ 用户 ID。
        :param size: 头像尺寸(支持140,640)。
        """
        api = '/g'
        method = 'GET'
        download_avatar_headers = self.headers.download_avatar_headers
        params = {
            'b': 'qq',
            'nk': str(user_id),
            's': str(size)
        }

        default_avatar_path = os.path.join(base_path, 'image', 'default_avatar.jpg')

        try:
            resp, content = self.qlogo_request.sendRequest(api, method, params=params, body=None, headers=download_avatar_headers)
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

    def upload_kl_file(self, file_name, upload_data):
        # 1、获取token
        get_token_api = '/api/upload/issue/token'
        method = 'GET'
        kl_main_headers = self.headers.kl_main_headers
        kl_main_headers['cookie'] = self.kl_cookies
        get_token_params = {
            'filename': str(file_name)
        }
        resp, content = self.kl_request.sendRequest(get_token_api, method, params=get_token_params, body=None,
                                                    headers=kl_main_headers)
        get_token_data = json.loads(content).get('data')
        upload_endopint = get_token_data.get('httpEndpoints')[0]
        token = get_token_data.get('token')
        print(upload_endopint, token)

        # 2、开始上传图片
        kl_upload_file_headers = self.headers.kl_upload_file_headers
        upload_file_request = RequestClient(upload_endopint)
        upload_file_api = '/api/upload/fragment'
        method = 'POST'
        upload_file_params = {
            'upload_token': token,
            'fragment_id': 0
        }
        resp, content = upload_file_request.sendRequest(upload_file_api, method, params=upload_file_params,
                                                        body=upload_data, headers=kl_upload_file_headers)
        upload_file_data = json.loads(content)
        print(upload_file_data)

        # 3、结束上传
        complete_file_api = '/api/upload/complete'
        method = 'POST'
        complete_file_params = {
            'fragment_count': 1,
            'upload_token': token
        }
        resp, content = self.kuaishouzt_request.sendRequest(complete_file_api, method, params=complete_file_params,
                                                            body=None, headers=kl_upload_file_headers)
        upload_file_data = json.loads(content)
        print(upload_file_data)

        # 4、完成上传
        verify_file_api = '/api/upload/verify/token'
        method = 'GET'
        verify_file_params = {
            'token': token
        }
        resp, content = self.kl_request.sendRequest(verify_file_api, method, params=verify_file_params, body=None,
                                                    headers=kl_main_headers)
        verify_file_data = json.loads(content).get('data')
        image_url = verify_file_data.get('url')
        print(image_url)

        return image_url

    def start_kl_generation(self, image_url, positive_prompt, negative_prompt=None, cfg=None):
        # 不提供negative_prompt、cfg的话，则使用默认
        if not negative_prompt:
            negative_prompt = "模糊、变形、毁容、低质量、拼贴、粒状、标志、抽象、插图、计算机生成、扭曲"
        if not cfg:
            cfg = '0.5'
        data = {
            # 高质量
            # "type": "m2v_img2video_hq",
            # 普通质量
            "type": "m2v_img2video",
            "arguments": [
                {
                    "name": "prompt",
                    "value": str(positive_prompt)
                },
                # {
                #     "name": "rich_prompt",
                #     "value": str(positive_prompt)
                # },
                {
                    "name": "negative_prompt",
                    "value": str(negative_prompt)
                },
                {
                    "name": "cfg",
                    "value": str(cfg)
                },
                {
                    "name": "duration",
                    "value": "5"
                },
                {
                    "name": "imageCount",
                    "value": "1"
                },
                {
                    "name": "kling_version",
                    "value": "1.6"
                },
                {
                    "name": "tail_image_enabled",
                    "value": "false"
                },
                {
                    "name": "camera_json",
                    "value": "{\"type\":\"empty\",\"horizontal\":0,\"vertical\":0,\"zoom\":0,\"tilt\":0,\"pan\":0,\"roll\":0}"
                },
                {
                    "name": "camera_control_enabled",
                    "value": "false"
                },
                {
                    "name": "biz",
                    "value": "klingai"
                }
            ],
            "inputs": [
                {
                    "inputType": "URL",
                    "url": str(image_url),
                    "name": "input"
                }
            ]
        }

        api = '/api/task/submit'
        method = 'POST'
        kl_main_headers = self.headers.kl_main_headers
        kl_main_headers['cookie'] = self.kl_cookies
        resp, content = self.kl_request.sendRequest(api, method, params=None, body=data,
                                                    headers=kl_main_headers)
        response_data = json.loads(content).get('data')
        print(response_data)

        status_code = resp.get("status")
        if status_code != '200':
            return {
                'success': 'fail',
                'msg': resp.get("message")
            }

        task = response_data.get('task')
        task_id = task.get('id')
        print(task_id)

    def generate_viggle_sign(self, params=None, data=None):
        data_string = ''
        if params is not None:
            # 使用列表推导和字符串拼接来格式化
            data_string = ''.join([f'{key}=[{value}]' for key, value in params.items()])
        if data is not None:
            # 使用 json.dumps() 转换为 JSON 字符串
            data_string = json.dumps(data)
        # 生成时间戳（毫秒级）
        timestamp = str(int(time.time() * 1000))
        # 生成 UUID（版本4）
        unique_uuid = str(uuid.uuid4())
        # 固定的字符串部分
        fixed_pre = '537.36'
        fixed_suf = 'qdsnfXVFGS1dVCYTju'
        # 拼接字符串
        sign_string = timestamp + unique_uuid + fixed_pre + data_string + fixed_suf
        # 使用 MD5 加密
        sign = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
        return timestamp, unique_uuid, sign

    async def upload_viggle_image(self, file_name, upload_data):
        boundary = '--WebKitFormBoundaryi2EVb79ueFSd1lJY'
        # 生成签名
        timestamp, unique_uuid, sign = self.generate_viggle_sign()
        # 准备headers
        headers = self.headers.viggle_upload_file_headers
        headers['s'] = sign
        headers['u'] = unique_uuid
        headers['t'] = timestamp
        headers['authorization'] = self.viggle_key
        headers['content-type'] = 'multipart/form-data; boundary={}'.format(boundary)

        # 准备body，构建multipart/form-data的请求体
        # 存储各个部分的列表
        dataList = []
        # 1. 添加boundary
        dataList.append(encode('--' + boundary))
        # 2. 添加Content-Disposition头，指定字段名和文件名
        dataList.append(
            encode('Content-Disposition: form-data; name="file"; filename="{0}"'.format(file_name.split('/')[-1])))
        # 3. 获取文件的 MIME 类型
        file_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
        dataList.append(encode('Content-Type: {}'.format(file_type)))
        # 4. 添加一个空行（表示header和文件内容之间的分隔）
        dataList.append(encode(''))
        # 5. 将文件内容加入到dataList中
        dataList.append(upload_data)
        # 6. 结束boundary，表示请求体的结束
        dataList.append(encode('--' + boundary + '--'))
        # 7. 添加一个空行（表示请求体的结束）
        dataList.append(encode(''))
        # 8. 将所有部分合并成最终的请求体
        body = b'\r\n'.join(dataList)

        upload_viggle_image_api = '/api/asset/image'
        method = 'POST'
        resp, content = await self.viggle_request.sendRequest(upload_viggle_image_api, method, body=body,
                                            headers=headers)
        if str(resp.status_code) == '200':
            data = json.loads(content).get('data')
            msg = json.loads(content).get("message")
            print(f'请求结果：{msg}, name:{data.get("name")}, task_id:{data.get("id")}, url:{data.get("url")}')
            task_id = data.get('id')
            return task_id
        else:
            return None

    async def upload_viggle_video(self, file_name):
        boundary = '--WebKitFormBoundaryi2EVb79ueFSd1lJY'
        # 生成签名
        timestamp, unique_uuid, sign = self.generate_viggle_sign()
        # 准备headers
        headers = self.headers.viggle_upload_file_headers
        headers['s'] = sign
        headers['u'] = unique_uuid
        headers['t'] = timestamp
        headers['authorization'] = self.viggle_key
        headers['content-type'] = 'multipart/form-data; boundary={}'.format(boundary)

        # 准备body，构建multipart/form-data的请求体
        # 存储各个部分的列表
        dataList = []
        # 1. 添加boundary
        dataList.append(encode('--' + boundary))
        # 2. 添加Content-Disposition头，指定字段名和文件名
        dataList.append(
            encode('Content-Disposition: form-data; name="file"; filename="{0}"'.format(file_name.split('/')[-1])))
        # 3. 获取文件的 MIME 类型
        file_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
        dataList.append(encode('Content-Type: {}'.format(file_type)))
        # 4. 添加一个空行（表示header和文件内容之间的分隔）
        dataList.append(encode(''))
        # 5. 读取文件内容并加入到dataList中
        with open(file_name, 'rb') as f:
            dataList.append(f.read())
        # 6. 结束boundary，表示请求体的结束
        dataList.append(encode('--' + boundary + '--'))
        # 7. 添加一个空行（表示请求体的结束）
        dataList.append(encode(''))
        # 8. 将所有部分合并成最终的请求体
        body = b'\r\n'.join(dataList)

        upload_viggle_image_api = '/api/asset/video'
        method = 'POST'
        resp, content = await self.viggle_request.sendRequest(upload_viggle_image_api, method, body=body,
                                            headers=headers)
        data = json.loads(content).get('data')
        msg = json.loads(content).get("message")
        print(f'请求结果：{msg}, name:{data.get("name")}, task_id:{data.get("id")}, url:{data.get("url")}')
        task_id = data.get('id')
        return task_id

    async def start_viggle_generation(self, image_id, video_id):
        data = {
            "imageID": str(image_id),
            "bgMode": 2,
            "modelInfoID": 4,
            "watermark": 1,
            "videoID": str(video_id)
        }
        # 生成签名
        timestamp, unique_uuid, sign = self.generate_viggle_sign(data=data)
        # 准备headers
        headers = self.headers.viggle_main_headers
        headers['s'] = sign
        headers['u'] = unique_uuid
        headers['t'] = timestamp
        headers['authorization'] = self.viggle_key
        video_task_api = '/api/video-task'
        method = 'POST'
        resp, content = await self.viggle_request.sendRequest(video_task_api, method, body=data,
                                                        headers=headers)
        if str(resp.status_code) == '200':
            data = json.loads(content).get('data')
            msg = json.loads(content).get("message")
            print(f'请求结果：{msg}, taskID:{data.get("taskID")}')
            task_id = data.get("taskID")
            return task_id
        else:
            return None

    async def query_viggle_result(self, task_id):
        data = {
            "ids": [
                str(task_id)
            ]
        }
        # 生成签名
        timestamp, unique_uuid, sign = self.generate_viggle_sign(data=data)
        # 准备headers
        headers = self.headers.viggle_main_headers
        headers['s'] = sign
        headers['u'] = unique_uuid
        headers['t'] = timestamp
        headers['authorization'] = self.viggle_key
        query_viggle_result_api = '/api/video-task/by-ids'
        method = 'POST'
        resp, content = await self.viggle_request.sendRequest(query_viggle_result_api, method, body=data,
                                                        headers=headers)
        data = json.loads(content).get('data')
        msg = json.loads(content).get("message")
        result = data[0].get('result')
        if result != '':
            print(f'请求结果：{msg}, result:{result}')
            return result
        else:
            return None

    async def download_viggle_file(self, url):
        api = url.split('https://cdn.viggle.ai')[-1]
        method = 'GET'
        # 准备headers
        headers = self.headers.download_viggle_headers
        resp, content = self.vigglecdn_request.sendRequest(api, method, headers=headers,timeout=600)
        # 保存文件至本地
        # with open('downloaded_video.mp4', 'wb') as file:
        #     file.write(content)
        # 将二进制数据保存到变量download_data
        download_data = content
        return download_data

def main():
    s = Service()
    file_name = 'QQ图片20250114215122.png'
    with open(file_name, 'rb') as file:
        upload_data = file.read()
    task_id1 = s.upload_viggle_image(file_name, upload_data)
    # # file_name = 'QQ录屏20250112032045.mp4'
    # # task_id2 = s.upload_viggle_video(file_name)
    # task_id3 = s.start_viggle_generation(task_id1, "e70dc06d-5e98-41f6-a395-d09efa0734c0")
    # url = s.query_viggle_result('af0cc650-1854-49de-a7e3-fb358d4bbf6a')
    # s.download_viggle_file(url)


    # positive_prompt = '跳舞'
    # s.start_kl_generation(url, positive_prompt)

    # file_name = '8592halflength39685.png'
    # with open(file_name, 'rb') as file:
    #     upload_data = file.read()
    # url = s.upload_file(file_name, upload_data)
    #
    # positive_prompt = '跳舞'
    # s.start_kl_generation(url, positive_prompt)
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

if __name__ == '__main__':
    # main()
    pass
