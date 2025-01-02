from tortoise import fields, Tortoise
from tortoise.models import Model
from datetime import date


class Snapshot(Model):
    id = fields.IntField(pk=True, generated=True)
    image_name = fields.CharField(max_length=255)
    image_id = fields.CharField(max_length=255)
    image_data = fields.BinaryField()  # 使用 BinaryField 来存储二进制数据（例如图片）

    class Meta:
        table = "snapshotV2"  # 表名为 snapshot
        table_description = "图片快照数据表"

    def __str__(self):
        return f"{self.image_name}"

    @classmethod
    async def get_max_id(cls):
        # 获取数据库连接（默认数据库连接）
        connection = Tortoise.get_connection("default")
        # 执行原生 SQL 查询，获取最大 id
        result = await connection.execute_query_dict("SELECT MAX(id) AS max_id FROM snapshotV2")
        # 返回最大 id
        return result[0]['max_id'] if result else None


class Halflength(Model):
    id = fields.IntField(pk=True, generated=True)
    image_name = fields.CharField(max_length=255)
    image_id = fields.CharField(max_length=255)
    image_data = fields.BinaryField()  # 使用 BinaryField 来存储二进制数据（例如图片）

    class Meta:
        table = "halflengthV2"  # 表名为 halflength
        table_description = "资料快照数据表"

    def __str__(self):
        return f"{self.image_name}"


class DailyWife(Model):
    id = fields.IntField(pk=True, generated=True)
    user_id = fields.CharField(max_length=32)
    wife_id = fields.CharField(max_length=32)
    date = fields.DateField(default=date(2000, 1, 1))

    class Meta:
        table = "daily_wife"
        table_description = "老婆表"

    @classmethod
    async def get_latest_wife_record(cls, user_id: str):
        """
        检查给定 user_id 对应的记录
        :param user_id: 用户 ID
        :return: 返回 latest_record
        """
        # 获取该 user_id 对应的最新记录
        latest_record = await DailyWife.filter(user_id=user_id).order_by('-date').first()
        return latest_record

    @classmethod
    async def add_new_wife(cls, user_id: str, wife_id: str) -> bool:
        """
        插入一条新的老婆记录，日期为今天
        :param user_id: 用户 ID
        :param wife_id: 老婆的 ID
        :return: 插入成功返回 True，失败返回 False
        """
        # 使用 create 方法插入一条新记录
        await DailyWife.create(user_id=user_id, wife_id=wife_id, date=date.today())
        return True

    @classmethod
    async def check_wife(cls, wife_id: str):
        """
        查找老婆记录，日期为今天
        :param wife_id: 老婆的 ID
        :return: check_wife_record
        """
        check_wife_record = await DailyWife.filter(wife_id=wife_id, date=date.today()).first()
        return check_wife_record

