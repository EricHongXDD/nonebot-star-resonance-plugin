import os

from tortoise import fields, Tortoise
from tortoise.fields import Field
from tortoise.fields.base import VALUE
from tortoise.models import Model
from datetime import date, time, datetime, timedelta


class Snapshot(Model):
    id = fields.IntField(pk=True, generated=True)
    image_name = fields.CharField(max_length=255)
    image_id = fields.CharField(max_length=255)
    image_data = fields.BinaryField()  # 使用 BinaryField 来存储二进制数据（例如图片）
    sex = fields.CharField(max_length=4)

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


class DailyChildren(Model):
    id = fields.IntField(pk=True, generated=True)
    user_id = fields.CharField(max_length=255)
    my_wife_id = fields.CharField(max_length=255)
    my_daughter_wife_id = fields.CharField(max_length=255)
    my_daughter_id = fields.CharField(max_length=255)
    my_daughter2_id = fields.CharField(max_length=255)
    my_daughter2_wife_id = fields.CharField(max_length=255)
    my_granddaughter_id = fields.CharField(max_length=255)
    my_granddaughter2_id = fields.CharField(max_length=255)
    date = fields.DateField(default=date(2000, 1, 1))
    start_time = fields.TimeField(default=time(12, 0, 0))
    is_send = fields.CharField(max_length=32)

    class Meta:
        table = "daily_children"  # 表名为 daily_children
        table_description = "每日家庭关系表"

    def __str__(self):
        return f"{self.id}"

    @classmethod
    async def get_latest_record(cls, user_id: str):
        """
        检查给定 user_id 对应的记录
        :param user_id: 用户 ID
        :return: 返回 latest_record
        """
        # 获取该 user_id 对应的最新记录
        latest_record = await DailyChildren.filter(user_id=user_id).order_by('-date').first()
        return latest_record

    @classmethod
    async def add_new_relation(cls, user_id: str, my_wife_id: str = None, my_daughter_wife_id: str = None,
                               my_daughter_id: str = None, my_daughter2_id: str = None,
                               my_daughter2_wife_id: str = None, my_granddaughter_id: str = None,
                               my_granddaughter2_id: str = None) -> bool:
        """
        插入一条新的关系记录，日期为今天
        :param my_granddaughter2_id:
        :param my_granddaughter_id:
        :param my_daughter2_wife_id:
        :param my_daughter2_id:
        :param my_daughter_id:
        :param my_daughter_wife_id:
        :param my_wife_id:
        :param user_id: 用户 ID
        :return: 插入成功返回 True，失败返回 False
        """

        # 根据传入的参数构建插入的数据
        data = {
            "user_id": user_id,
            "my_wife_id": my_wife_id,
            "my_daughter_wife_id": my_daughter_wife_id,
            "my_daughter_id": my_daughter_id,
            "my_daughter2_id": my_daughter2_id,
            "my_daughter2_wife_id": my_daughter2_wife_id,
            "my_granddaughter_id": my_granddaughter_id,
            "my_granddaughter2_id": my_granddaughter2_id,
            "date": str(date.today()),
            "start_time": datetime.now().time().strftime('%H:%M:%S'),
            "is_send": "False",
        }

        # 过滤掉值为 None 的字段
        data = {key: value for key, value in data.items() if value is not None}

        # 构造 SQL 插入语句
        columns = ", ".join(data.keys())  # 获取列名
        values = ", ".join(
            [f"'{value}'" if isinstance(value, str) else str(value) for value in data.values()])  # 获取对应的值，并确保是字符串形式

        # 插入 SQL 语句
        sql = f"INSERT INTO daily_children ({columns}) VALUES ({values});"

        # 获取数据库连接
        connection = Tortoise.get_connection("default")

        # 执行原生 SQL 插入语句
        await connection.execute_query(sql)

        return True

    @classmethod
    async def update_relation(cls, user_id: str, date_str: str, my_wife_id: str = None, my_daughter_wife_id: str = None,
                              my_daughter_id: str = None, my_daughter2_id: str = None, my_daughter2_wife_id: str = None,
                              my_granddaughter_id: str = None, my_granddaughter2_id: str = None,
                              is_send: str = None) -> bool:
        """
        更新一条关系记录，根据 user_id 和 date 筛选并更新数据
        :param is_send: 是否发送过
        :param user_id: 用户 ID
        :param date_str: 日期，格式为 'YYYY-MM-DD'
        :param my_wife_id: 妻子 ID
        :param my_daughter_wife_id: 女儿的妻子 ID
        :param my_daughter_id: 女儿 ID
        :param my_daughter2_id: 第二个女儿 ID
        :param my_daughter2_wife_id: 第二个女儿的妻子 ID
        :param my_granddaughter_id: 孙女 ID
        :param my_granddaughter2_id: 第二个孙女 ID
        :return: 更新成功返回 True，失败返回 False
        """

        # 获取数据库连接
        connection = Tortoise.get_connection("default")

        # 构造更新的数据字典
        data = {
            "my_wife_id": my_wife_id,
            "my_daughter_wife_id": my_daughter_wife_id,
            "my_daughter_id": my_daughter_id,
            "my_daughter2_id": my_daughter2_id,
            "my_daughter2_wife_id": my_daughter2_wife_id,
            "my_granddaughter_id": my_granddaughter_id,
            "my_granddaughter2_id": my_granddaughter2_id,
            "is_send": is_send
        }

        # 过滤掉值为 None 的字段
        data = {key: value for key, value in data.items() if value is not None}

        # 如果没有提供任何要更新的字段，则不做任何更新
        if not data:
            return False

        # 构造 SQL 更新语句
        set_clause = ", ".join([f"{key} = '{value}'" if isinstance(value, str) else f"{key} = {value}"
                                for key, value in data.items()])  # 构造 SET 子句

        # 构建 WHERE 子句，确保是根据 user_id 和 date 筛选
        where_clause = f"user_id = '{user_id}' AND date = '{date_str}'"

        # 执行 SQL 更新语句
        sql = f"UPDATE daily_children SET {set_clause} WHERE {where_clause};"

        try:
            # 执行 SQL 更新
            await connection.execute_query(sql)
            return True
        except Exception as e:
            # 如果出现异常，打印错误并返回 False
            print(f"更新失败: {e}")
            return False


class TomorrowEngagement(Model):
    id = fields.IntField(pk=True, generated=True)
    user_id = fields.CharField(max_length=32)
    object_id = fields.CharField(max_length=32)
    date = fields.DateField(default=date(2000, 1, 1))

    class Meta:
        table = "tomorrow_engagement"
        table_description = "明日订婚表"

    @classmethod
    async def get_latest_object_record(cls, user_id: str):
        """
        检查给定 user_id 对应的记录
        :param user_id: 用户 ID
        :return: 返回 latest_record
        """
        # 获取该 user_id 对应的最新记录
        latest_record = await TomorrowEngagement.filter(user_id=user_id).order_by('-date').first()
        return latest_record

    @classmethod
    async def add_new_object(cls, user_id: str, object_id: str) -> bool:
        """
        插入一条新的订婚记录，日期为今天
        :param user_id: 用户 ID
        :param object_id: 对象的 ID
        :return: 插入成功返回 True，失败返回 False
        """
        # 使用 create 方法插入一条新记录
        await TomorrowEngagement.create(user_id=user_id, object_id=object_id, date=date.today())
        return True

    @classmethod
    async def check_object(cls, object_id: str):
        """
        查找对象订婚记录，日期为今天
        :param object_id: 对象的 ID
        :return: check_object
        """
        check_object_record = await TomorrowEngagement.filter(object_id=object_id, date=date.today()).first()
        return check_object_record

    @classmethod
    async def check_yesterday_object(cls, object_id: str):
        """
        查找对象订婚记录，日期为昨天
        :param object_id: 对象的 ID
        :return: check_object
        """
        # 获取昨天的日期
        yesterday = (date.today() - timedelta(days=1))
        check_object_record = await TomorrowEngagement.filter(object_id=object_id, date=yesterday).first()
        return check_object_record

    @classmethod
    async def get_yesterday_object_record(cls, user_id: str):
        """
        检查给定 user_id 对应的昨日记录
        :param user_id: 用户 ID
        :return: 返回 yesterday_record
        """
        # 获取昨天的日期
        yesterday = (date.today() - timedelta(days=1))
        yesterday_record = await TomorrowEngagement.filter(user_id=user_id, date=yesterday).first()
        return yesterday_record


class ViggleVideo(Model):
    id = fields.IntField(pk=True, generated=True)
    task_id = fields.CharField(max_length=64)
    file_name = fields.CharField(max_length=64)
    date = fields.DateField(default=date(2000, 1, 1))
    time = fields.TimeField(default=time(12, 0, 0))

    class Meta:
        table = "viggle_video"
        table_description = "ViggleVideo表"

    @classmethod
    async def add_new_record(cls, task_id: str, file_name: str) -> bool:
        """
        插入一条新的video上传记录
        :return: 插入完成后返回True
        """
        # 使用 create 方法插入一条新记录
        upload_time = datetime.now().time().strftime('%H:%M:%S')
        # 尝试查找是否已经有记录
        existing_record = await ViggleVideo.filter(file_name=file_name).first()

        if existing_record:
            # 如果记录已经存在，更新该记录
            await existing_record.update_from_dict({
                'task_id': task_id,
                'date': date.today(),
                'time': upload_time
            })
        else:
            # 如果没有记录，创建一条新记录
            await ViggleVideo.create(
                task_id=task_id,
                file_name=file_name,
                date=date.today(),
                time=upload_time
            )

        return True
    @classmethod
    async def check_record(cls, file_name: str) -> bool:
        """
        检查file_name上传时间是否>=12小时
        :return: >=12小时返回False，否则返回True
        """
        # 查询指定 file_name 的记录
        record = await ViggleVideo.filter(file_name=file_name).first()
        # 如果记录不存在，返回 False （因为没有记录上传时间）
        if not record:
            return False
        # 获取当前时间
        current_time = datetime.now().time()
        current_datetime = datetime.combine(date.today(), current_time)

        # 检查 record.time 是否是 datetime.time 类型
        if isinstance(record.time, timedelta):
            # 如果是 timedelta 类型，转换为 time 类型（假设 time 是从零点开始）
            record_time = (datetime.min + record.time).time()
        else:
            # 如果 record.time 本身是 time 类型，直接使用
            record_time = record.time

        # 获取上传时间
        record_datetime = datetime.combine(record.date, record_time)

        # 检查上传时间是否>=12小时
        # if (current_datetime - record_datetime) >= timedelta(hours=12):
        #     return False
        return True

    @classmethod
    async def query_task_id(cls, file_name: str) -> Field[VALUE] | VALUE | None:
        """
        通过file_name查询task_id
        :return: 查询成功返回task_id，否则返回None
        """
        # 查询指定 file_name 的记录
        record = await ViggleVideo.filter(file_name=file_name).first()

        # 如果找到记录，则返回 task_id
        if record:
            return record.task_id
        # 如果没有找到记录，返回 None
        return None

    @classmethod
    async def check_filename_exist(cls, file_name: str) -> bool:
        """
        检查filename字段值是否存在（忽略后缀）
        :return: 查询存在返回True，否则返回False
        """
        # 获取不带扩展名的文件名
        base_name = os.path.splitext(file_name)[0]

        # 查询数据库中所有文件名，不带扩展名后进行比对
        records = await ViggleVideo.filter(file_name__startswith=base_name).all()

        # 如果找到任何记录，表示存在匹配的文件名（忽略后缀）
        if records:
            return True
        return False

    @classmethod
    async def query_filename(cls) -> list:
        """
        查询数据库中所有filename列表（不返回后缀名）
        :return: filename列表
        """
        # 查询数据库中的所有 file_name 字段
        records = await ViggleVideo.all()

        # 获取所有去掉扩展名的 file_name
        file_names = [os.path.splitext(record.file_name)[0] for record in records]

        return file_names