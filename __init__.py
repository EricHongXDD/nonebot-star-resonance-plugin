import os
import base64
from io import BytesIO
from nonebot import on_command
from nonebot import on_regex
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.plugin import PluginMetadata
from nonebot_plugin_tortoise_orm import add_model

from .data_source import get_snapshot_by_id, get_halflength_by_id, find_wife_by_qq, give_wife_sora

# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="send_bpm_pic",
    description="根据用户 ID 查询 snapshot 并返回对应的 Base64 图片",
    usage="使用指令：查询{id} 来获取图片",
)

# 注册插件模型
add_model("plugins.send_bpm_pic.models")


# 查询指令
send_snapshot = on_regex("查询头像", priority=5, block=True, rule=to_me())
send_halflength = on_regex("查询资料", priority=5, block=True, rule=to_me())
find_wife = on_regex("今日老婆", priority=5, block=True, rule=to_me())


# 查询逻辑
async def send_images(qq_id, user_id, bpm_pics, max_images=5):
    """ 发送图片的通用函数，最多发送 max_images 张 """
    pic_num = 0
    all_num = len(bpm_pics)
    for bpm_pic in bpm_pics:
        if pic_num < max_images:
            messages = [
                MessageSegment.at(qq_id),
                f'用户ID {user_id} 的查询结果为:',
                MessageSegment.image(BytesIO(bpm_pic["image_data"])),
                f'{pic_num + 1}/{all_num}'
            ]
            await send_halflength.send(Message(messages))
            pic_num += 1
        else:
            messages = [
                MessageSegment.at(qq_id),
                "图片超过5张，已发送近期的5张图片"
            ]
            await send_halflength.send(Message(messages))
            break


async def handle_query(event: MessageEvent, query_type: str, query_func):
    """ 通用的查询处理函数 """
    qq_id = str(event.user_id)
    msg = str(event.get_message()).strip().replace(' ', '')

    # 提取用户ID并验证
    try:
        user_id = msg.split(query_type)[1].strip()
    except IndexError:
        messages = [
            MessageSegment.at(qq_id),
            f"请提供用户ID，例如：{query_type}1234"
        ]
        await send_halflength.finish(Message(messages))
        return

    if not user_id.isdigit():
        messages = [
            MessageSegment.at(qq_id),
            "用户ID格式不正确"
        ]
        await send_halflength.finish(Message(messages))
        return

    # 获取数据库中的图片
    bpm_pics = await query_func(user_id)
    if bpm_pics:
        await send_images(qq_id, user_id, bpm_pics)
    else:
        messages = [
            MessageSegment.at(qq_id),
            "没有查询到相关图片，欢迎贡献C:\\Users\\改为实际用户名\\AppData\\Local\\Temp\\bokura\\Star\\http文件夹增加数据~"
        ]
        await send_halflength.finish(Message(messages))


@send_snapshot.handle()
async def handle_snapshot(event: MessageEvent):
    """ 处理查询头像的请求 """
    await handle_query(event, "查询头像", get_snapshot_by_id)


@send_halflength.handle()
async def handle_halflength(event: MessageEvent):
    """ 处理查询资料的请求 """
    await handle_query(event, "查询资料", get_halflength_by_id)


async def send_wife_info(event, user_id, image_data, wife_id, custom_msg=None):
    """构建并发送老婆信息"""
    messages = []
    messages.append(MessageSegment.at(user_id))
    if custom_msg:
        messages.append(custom_msg)
    else:
        messages.append("今日的老婆是：\n")
    messages.append(MessageSegment.image(BytesIO(image_data)))
    messages.append(f"\nTa在内测时的ID是{wife_id}，快去开拓局的民政中心领证吧！")
    await find_wife.finish(Message(messages))


async def handle_same_status(event, user_id, retry_times, data):
    """处理status为'same'的情况"""
    messages = data.get("msg")
    await find_wife.send(Message(messages))

    while retry_times < 2:
        retry_times += 1
        data = await find_wife_by_qq(user_id)
        status = data.get("status")
        if status == 'success':
            image_data = data.get("image_data")
            wife_id = data.get("wife_id")
            await send_wife_info(event, user_id, image_data, wife_id)
            return
        else:
            messages = data.get("msg")
            await find_wife.send(Message(messages))
    return retry_times


@find_wife.handle()
async def _(event: MessageEvent):
    # 用户 ID (字符串类型，用于 @)
    user_id = str(event.user_id)

    # 获取数据库中的图片
    data = await find_wife_by_qq(user_id)
    status = data.get("status")

    if status == 'success':
        image_data = data.get("image_data")
        wife_id = data.get("wife_id")
        await send_wife_info(event, user_id, image_data, wife_id)

    elif status == 'fail':
        messages = []
        messages.append(MessageSegment.at(user_id))
        messages.append(data.get("msg"))
        await find_wife.finish(Message(messages))

    elif status == 'same':
        retry_times = 1
        retry_times = await handle_same_status(event, user_id, retry_times, data)

        if retry_times == 2:
            # 如果retry_times为2，说明已经重试过2次，还未获取到有效的老婆信息
            messages = []
            messages.append(MessageSegment.at(user_id))
            messages.append(f"诶呀，今天已经给你挑了{retry_times}位老婆了，但她们都名花有主了，那就把穹妹许配给你吧~")
            await find_wife.send(Message(messages))

            # 给穹妹
            data = await give_wife_sora(user_id)
            if not data.get("wife_id"):
                await find_wife.finish("wife_id为空异常退出")

            image_data = data.get("image_data")
            wife_id = data.get("wife_id")
            await send_wife_info(event, user_id, image_data, wife_id)



