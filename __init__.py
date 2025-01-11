import os
import base64
import random
from datetime import date, datetime, timedelta
from io import BytesIO
from nonebot import on_command, on_fullmatch
from nonebot import on_regex
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.plugin import PluginMetadata
from nonebot_plugin_tortoise_orm import add_model
from .service import Service
from .models import DailyWife, DailyChildren, TomorrowEngagement
from .data_source import get_snapshot_by_id, get_halflength_by_id, find_wife_by_qq, give_wife_sora, get_wife_snapshot, \
    engage

# 插件元数据
__plugin_meta__ = PluginMetadata(
    name="nonebot-star-resonance-plugin",
    description="星痕共鸣相关插件",
    usage="使用指令：查询头像{user_id}、查询资料{user_id}、今日老婆、生儿育女",
)

# 注册插件模型
add_model("plugins.send_bpm_pic.models")


# 查询指令
send_snapshot = on_regex("查询头像", priority=5, block=True, rule=to_me())
send_halflength = on_regex("查询资料", priority=5, block=True, rule=to_me())
# find_wife = on_regex("今日老婆", priority=5, block=True, rule=to_me())
having_children = on_regex("生儿育女", priority=5, block=True, rule=to_me())
get_relation = on_regex("查询子女", priority=5, block=True, rule=to_me())
# 注册今日配偶事件
daily_wife_husband_triggers = ['今日老婆','今日老公','今日配偶']
daily_wife_husband_events = [
    on_fullmatch(trigger.strip(), priority=5, block=True, rule=to_me()) for trigger in daily_wife_husband_triggers
]
# 注册订婚事件
tomorrow_engagement = on_regex("订婚", priority=5, block=True, rule=to_me())

for find_wife in daily_wife_husband_events:
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
                messages.append(f"诶呀，今天已经给你挑了{retry_times}位配偶了，但她们都名花有主了，那就把穹妹许配给你吧~")
                await find_wife.send(Message(messages))

                # 给穹妹
                data = await give_wife_sora(user_id)
                if not data.get("wife_id"):
                    await find_wife.finish("wife_id为空异常退出")

                image_data = data.get("image_data")
                wife_id = data.get("wife_id")
                await send_wife_info(event, user_id, image_data, wife_id)

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
        messages.append("今日的配偶是：\n")
    messages.append(MessageSegment.image(BytesIO(image_data)))
    messages.append(f"\nTa在内测时的ID是{wife_id}，快去开拓局的民政中心领证吧！（也许，也可以做一些别的...？）")
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


@having_children.handle()
async def _(event: MessageEvent):
    # 用户 ID (字符串类型，用于 @)
    user_id = str(event.user_id)
    user_name = event.sender.nickname  # 用户昵称

    # 先判断是否有配偶
    latest_wife_record = await DailyWife.get_latest_wife_record(user_id)
    # 如果今天没有配偶，直接结束事件
    if not (latest_wife_record and latest_wife_record.date == date.today()):
        messages = []
        messages.append(MessageSegment.at(user_id))
        messages.append('你今天还没有配偶，不能做这种事哦！')
        await having_children.finish(Message(messages))

    # 再判断有没有生成过关系
    latest_relation_record = await DailyChildren.get_latest_record(user_id)
    # 如果今天生成过，直接结束事件
    if latest_relation_record and latest_relation_record.date == date.today():
        messages = []
        messages.append(MessageSegment.at(user_id))
        messages.append('你今天已经做过这种事啦！要爱惜身体哦！')
        await having_children.finish(Message(messages))

    # 如果今天有配偶且没有生成过关系，开始插入数据，记录开始时间
    my_wife_id = latest_wife_record.wife_id
    is_success = await DailyChildren.add_new_relation(
        user_id=str(user_id),
        my_wife_id=str(my_wife_id),
    )

    # 返回消息
    messages = []
    messages.append(MessageSegment.at(user_id))
    messages.append('正在进行传宗接代...请等待3分钟~')
    await having_children.finish(Message(messages))


@get_relation.handle()
async def _(event: MessageEvent):
    # 等待时间（单位分钟）
    wait_time = 3
    # 用户 ID (字符串类型，用于 @)
    user_id = str(event.user_id)
    user_name = event.sender.nickname  # 用户昵称

    # 先判断是否有配偶
    latest_wife_record = await DailyWife.get_latest_wife_record(user_id)
    # 如果今天没有配偶，直接结束事件
    if not (latest_wife_record and latest_wife_record.date == date.today()):
        messages = []
        messages.append(MessageSegment.at(user_id))
        messages.append('你今天还没有配偶，快去结婚吧！')
        await get_relation.finish(Message(messages))

    # 再判断有没有生成过关系
    latest_relation_record = await DailyChildren.get_latest_record(user_id)
    # 如果今天没有生成过，直接结束事件
    if not(latest_relation_record and latest_relation_record.date == date.today()):
        messages = []
        messages.append(MessageSegment.at(user_id))
        messages.append('你今天还没有传宗接代哦！快去生儿育女吧！')
        await get_relation.finish(Message(messages))

    # 继续判断有没有发送过关系信息
    # 如果今天发送过，直接结束事件
    if latest_relation_record.is_send == 'True':
        messages = []
        messages.append(MessageSegment.at(user_id))
        messages.append('今天已经发送过你的家庭成员信息啦~要好好记住哦！')
        await get_relation.finish(Message(messages))

    # 继续判断现在时间-创建时间是否大于1小时
    # 如果时间小于1小时，直接结束事件
    start_time = latest_relation_record.start_time
    # 当前时间
    current_time = datetime.now()
    # 将时间字符串转换为 datetime 对象
    time_object = datetime.strptime(str(start_time), "%H:%M:%S")
    # 由于 time_object 默认是今天的时间，通过对比两者来计算差值
    time_object = time_object.replace(year=current_time.year, month=current_time.month, day=current_time.day)
    # 计算当前时间与给定时间之间的时间差
    time_diff = current_time - time_object

    if time_diff < timedelta(minutes=wait_time):
        # 计算剩余分钟数
        remaining_minutes = (time_diff.total_seconds() / 60)
        messages = []
        messages.append(MessageSegment.at(user_id))
        messages.append(f'还在进行传宗接代，难道你好了？（请继续等待 {wait_time-int(abs(remaining_minutes))} 分钟）')
        await get_relation.finish(Message(messages))

    # 如果今天有配偶且没有生成过关系，开始随机生成关系
    # 1、获取用户头像
    s = Service()
    my_avatar = s.download_avatar(user_id, 140)

    # 2、获取配偶头像、id
    my_wife_id = latest_wife_record.wife_id
    # 获取数据库中的图片
    bpm_pics = await get_snapshot_by_id(my_wife_id)
    # 检查列表是否有元素并随机取一个
    if bpm_pics and len(bpm_pics) > 1:
        my_wife_avatar = random.choice(bpm_pics)["image_data"]
    else:
        # 如果列表为空或只有一个元素，直接取第一个
        my_wife_avatar = bpm_pics[0]["image_data"] if bpm_pics else None

    # 3、获取其他亲属关系头像、id
    my_daughter_wife_snapshot = await get_wife_snapshot()
    my_daughter_wife_avatar = my_daughter_wife_snapshot.image_data
    my_daughter_wife_id = my_daughter_wife_snapshot.image_name.split("snapshot")[0]

    my_daughter_snapshot = await get_wife_snapshot()
    my_daughter_avatar = my_daughter_snapshot.image_data
    my_daughter_id = my_daughter_snapshot.image_name.split("snapshot")[0]

    my_daughter2_snapshot = await get_wife_snapshot()
    my_daughter2_avatar = my_daughter2_snapshot.image_data
    my_daughter2_id = my_daughter2_snapshot.image_name.split("snapshot")[0]

    my_daughter2_wife_snapshot = await get_wife_snapshot()
    my_daughter2_wife_avatar = my_daughter2_wife_snapshot.image_data
    my_daughter2_wife_id = my_daughter2_wife_snapshot.image_name.split("snapshot")[0]

    my_granddaughter_snapshot = await get_wife_snapshot()
    my_granddaughter_avatar = my_granddaughter_snapshot.image_data
    my_granddaughter_id = my_granddaughter_snapshot.image_name.split("snapshot")[0]

    my_granddaughter2_snapshot = await get_wife_snapshot()
    my_granddaughter2_avatar = my_granddaughter2_snapshot.image_data
    my_granddaughter2_id = my_granddaughter2_snapshot.image_name.split("snapshot")[0]
    # 4、生成关系图、关系文本
    avatar_data = []
    avatar_data.append(my_avatar)
    avatar_data.append(my_wife_avatar)

    avatar_data.append(my_daughter_wife_avatar)
    avatar_data.append(my_daughter_avatar)
    avatar_data.append(my_daughter2_wife_avatar)
    avatar_data.append(my_daughter2_avatar)

    avatar_data.append(my_granddaughter_avatar)
    avatar_data.append(my_granddaughter2_avatar)

    relation_pic = await s.process_image(avatar_data, user_name)
    avatar_desc = f'祝贺你喜添家丁！你的家庭成员具体ID如下：\n' \
                  f'配偶：{my_wife_id}\n' \
                  f'儿媳/女婿a：{my_daughter_wife_id}\n' \
                  f'儿子/儿女a：{my_daughter_id}\n' \
                  f'儿子/儿女b：{my_daughter2_id}\n' \
                  f'儿媳/女婿b：{my_daughter2_wife_id}\n' \
                  f'孙子/孙女a：{my_granddaughter_id}\n' \
                  f'孙子/孙女b：{my_granddaughter2_id}'

    # 更新数据
    # new_data = {
    #     'my_wife_id': str(my_wife_id),
    #     'my_daughter_wife_id': str(my_daughter_wife_id),
    #     'my_daughter_id': str(my_daughter_id),
    #     'my_daughter2_id': str(my_daughter2_id),
    #     'my_daughter2_wife_id': str(my_daughter2_wife_id),
    #     'my_granddaughter_id': str(my_granddaughter_id),
    #     'my_granddaughter2_id': str(my_granddaughter2_id),
    #     'is_send': 'True'
    # }

    await DailyChildren.update_relation(
        user_id=str(user_id),
        date_str=str(date.today()),
        my_wife_id=str(my_wife_id),
        my_daughter_id=str(my_daughter_id),
        my_daughter_wife_id=str(my_daughter_wife_id),
        my_daughter2_id=str(my_daughter2_id),
        my_daughter2_wife_id=str(my_daughter2_wife_id),
        my_granddaughter_id=str(my_granddaughter_id),
        my_granddaughter2_id=str(my_granddaughter2_id),
        is_send='True',
    )

    # 返回消息
    messages = []
    messages.append(MessageSegment.at(user_id))
    messages.append(avatar_desc)
    await get_relation.send(Message(messages))
    messages = []
    messages.append(MessageSegment.at(user_id))
    messages.append(MessageSegment.image(BytesIO(relation_pic)))
    await get_relation.finish(Message(messages))


@tomorrow_engagement.handle()
async def _(event: MessageEvent):
    """ 订婚处理函数 """
    qq_id = str(event.user_id)
    msg = str(event.get_message()).strip().replace(' ', '')

    # 提取用户ID并验证
    try:
        object_id = msg.split('订婚')[1].strip()
    except IndexError:
        messages = [
            MessageSegment.at(qq_id),
            f"请提供用户ID，例如：订婚1234"
        ]
        await tomorrow_engagement.finish(Message(messages))
        return

    if not object_id.isdigit():
        messages = [
            MessageSegment.at(qq_id),
            "用户ID格式不正确"
        ]
        await tomorrow_engagement.finish(Message(messages))
        return

    # 订婚处理
    result = await engage(qq_id, object_id)
    msg = result['msg']
    # 返回消息
    messages = [
        MessageSegment.at(qq_id),
        f"{msg}"
    ]
    await tomorrow_engagement.finish(Message(messages))
    return
