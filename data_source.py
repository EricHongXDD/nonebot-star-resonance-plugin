import random
from datetime import date
from typing import List
from .models import Snapshot, Halflength, DailyWife, TomorrowEngagement
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment


async def get_snapshot_by_id(id: str) -> List[dict]:
    """
    根据用户提供的 id 查找 name 字段中含有 {id} 的条目，并返回 二进制 编码的 snapshot 图片。
    """
    try:
        # 查询 snapshot 中 image_name 字段包含 {id} 的条目
        # snapshots = await Snapshot.filter(image_name__startswith=f"{id}snapshot").values("image_data", "image_name")
        # snapshots = await Snapshot.get_or_create(image_name=f"{id}snapshot")
        snapshots = await Snapshot.filter(image_name=f"{id}snapshot").values\
            ("id", "image_data", "image_id", "image_name")
        if snapshots:
            # 使用 'order_by' 排序结果，以 image_id 降序排列
            snapshots_sorted = sorted(snapshots, key=lambda x: x['image_id'], reverse=True)
            return snapshots_sorted
        else:
            return []
    except Exception as e:
        logger.error(f"查询 snapshot 图片时发生错误: {e}")
        return []


async def get_halflength_by_id(id: str) -> List[dict]:
    """
    根据用户提供的 id 查找 image_name 字段中含有 {id} 的条目，并返回 二进制 编码的 halflength 图片。
    """
    try:
        # 查询 halflength 中 name 字段包含 {id} 的条目
        # halflengths = await Halflength.filter(image_name__startswith=f"{id}halflength").values("image_data", "image_name")
        # halflengths = await Halflength.get_or_create(image_name=f"{id}halflength")
        halflengths = await Halflength.filter(image_name=f"{id}halflength").values\
            ("image_data", "image_id", "image_name")

        if halflengths:
            # 使用 'order_by' 排序结果，以 image_id 降序排列
            halflengths_sorted = sorted(halflengths, key=lambda x: x['image_id'], reverse=True)
            return halflengths_sorted
        else:
            return []
    except Exception as e:
        logger.error(f"查询 snapshot 图片时发生错误: {e}")
        return []


async def get_wife_snapshot():
    """ 获取随机老婆的快照，封装了查询逻辑 """
    # 获取 snapshot 表的最大 ID
    max_id = await Snapshot.get_max_id()
    snapshot = None

    # 循环直到查询到一个有效的 snapshot
    while snapshot is None:
        random_id = random.randint(1, max_id)
        snapshot = await Snapshot.filter(id=str(random_id)).first()

    return snapshot


async def assign_wife_to_user(user_id: str, wife_id: str, snapshot) -> dict:
    """ 将老婆信息添加到 DailyWife 中并返回结果 """
    try:
        # 插入用户生成老婆的信息
        is_successful = await DailyWife.add_new_wife(user_id, wife_id)
        if not is_successful:
            return {
                "status": 'fail',
                "msg": '糟糕，你的配偶逃走了，试试换一个吧......'
            }

        # 返回老婆信息
        return {
            "status": 'success',
            "wife_id": wife_id,
            "image_name": snapshot.image_name,
            "image_data": snapshot.image_data
        }
    except Exception as e:
        logger.error(f"糟糕，你的配偶逃走了:{e}，试试换一个吧......")
        return {
            "status": 'fail',
            "msg": f"糟糕，你的配偶逃走了:{e}，试试换一个吧......"
        }


async def find_wife_by_qq(user_id: str) -> dict:
    """ 随机从 snapshot 表中选取一条数据并返回 base64 编码的 snapshot 图片 """
    try:
        # 获取最新的老婆记录
        latest_record = await DailyWife.get_latest_wife_record(user_id)

        # 如果今天已经有老婆
        if latest_record and latest_record.date == date.today():
            return {
                "status": 'fail',
                "msg": f'今天已经有配偶啦！你配偶在内测时的ID是{latest_record.wife_id}，不能开后宫哦！（也许，也可以做一些别的...？）'
            }

        # 查询昨日是否订婚
        object_record = await TomorrowEngagement.get_yesterday_object_record(user_id)
        if object_record:
            wife_id = object_record.object_id
            snapshots = await get_snapshot_by_id(wife_id)
            if snapshots:
                snapshot = random.choice(snapshots)
                id = snapshot['id']
                snapshot = await Snapshot.filter(id=str(id)).first()
            else:
                snapshot = None
        else:
            # 随机获取老婆快照
            snapshot = await get_wife_snapshot()

        if snapshot:
            wife_id = snapshot.image_name.split("snapshot")[0]
            # wife_id = '206924'

            # 查询昨日是否已经订婚
            is_others_object_record = await TomorrowEngagement.check_yesterday_object(wife_id)
            if is_others_object_record and is_others_object_record.user_id != user_id:
                return {
                    "status": 'same',
                    "msg": [
                        MessageSegment.at(user_id),
                        f"本来想给你许配的配偶在内测时的ID是{wife_id}，可惜Ta今天已经和",
                        MessageSegment.at(is_others_object_record.user_id),
                        '订婚了\n让我给你许配一位新的配偶吧！'
                    ]
                }
            # 查询是否已经是别人老婆
            is_others_wife_record = await DailyWife.check_wife(wife_id)
            if is_others_wife_record:
                return {
                    "status": 'same',
                    "msg": [
                        MessageSegment.at(user_id),
                        f"本来想给你许配的配偶在内测时的ID是{wife_id}，可惜Ta今天已经名花有主属于",
                        MessageSegment.at(is_others_wife_record.user_id),
                        '了\n让我给你许配一位新的配偶吧！'
                    ]
                }
            # 给用户分配老婆并返回结果
            return await assign_wife_to_user(user_id, wife_id, snapshot)

        else:
            return {
                "status": 'fail',
                "msg": '获取snapshot时出现服务内部错误'
            }

    except Exception as e:
        logger.error(f"查询随机 snapshot 图片时发生错误: {e}")
        return {
            "status": 'fail',
            "msg": f"查询随机 snapshot 图片时发生错误: {e}"
        }


async def give_wife_sora(user_id: str) -> dict:
    """
    给用户分配一个特定的老婆（ID：207344），并返回其信息。
    """
    try:
        wife_id = "207344"
        snapshot = await Snapshot.filter(image_name='207344snapshot').first()

        # 给用户分配老婆并返回结果
        return await assign_wife_to_user(user_id, wife_id, snapshot)

    except Exception as e:
        logger.error(f"查询 207344snapshot 图片时发生错误: {e}")
        return {
            "status": 'fail',
            "msg": f"查询 207344snapshot 图片时发生错误: {e}"
        }


async def engage(qq_id: str, object_id: str) -> dict:
    """ 随机从 snapshot 表中选取一条数据并返回 base64 编码的 snapshot 图片 """
    try:
        # 获取最新的订婚记录
        latest_record = await TomorrowEngagement.get_latest_object_record(qq_id)

        # 如果今天已经有订婚记录
        if latest_record and latest_record.date == date.today():
            return {
                "status": 'fail',
                "msg": f'今天已经和对象订婚啦！你对象在内测时的ID是{latest_record.object_id}，不能吃着碗里的还看着锅里的哦！'
            }

        # 检查对象id是否存在
        snapshots = await Snapshot.filter(image_name=f"{object_id}snapshot").values("image_data", "image_id", "image_name")
        if not snapshots:
            return {
                "status": 'fail',
                "msg": f'订婚对象身份ID：{object_id}在数据库中找不到哦！'
            }

        # 检查对象今日是否已经订婚
        check_object_record = await TomorrowEngagement.check_object(object_id)
        if check_object_record:
            return {
                "status": 'fail',
                "msg": f'晚啦！身份ID：{object_id}在今日已经和别人订婚了哦！'
            }

        # 添加订婚数据
        await TomorrowEngagement.add_new_object(qq_id, object_id)
        return {
            "status": 'success',
            "msg": f'和对象订婚成功，婚期为明天！你对象在内测时的ID是{object_id}'
        }

    except Exception as e:
        logger.error(f"订婚时发生错误: {e}")
        return {
            "status": 'fail',
            "msg": f"订婚时发生错误: {e}"
        }

