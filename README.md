# nonebot-star-resonance-plugin

基于nonebot框架（https://nonebot.dev
）的插件，涉及星痕共鸣相关功能。

## 目前功能：
通过 @bot 监听事件，支持以下操作：

1. 查询头像 `{用户id}`
2. 查询资料 `{用户id}`
3. 今日老婆 | 今日老公 | 今日配偶
4. 生儿育女
5. 查询子女

> 注：
> - 第 4 项功能需要先进行第 3 项操作。
> - 第 5 项功能需要先进行第 4 项操作。

## 数据模型：

### snapshotV2
```python
id = fields.IntField(pk=True, generated=True)
image_name = fields.CharField(max_length=255)
image_id = fields.CharField(max_length=255)
image_data = fields.BinaryField()  # 使用 BinaryField 来存储二进制数据（例如图片）
```

### halflengthV2
```python
id = fields.IntField(pk=True, generated=True)
image_name = fields.CharField(max_length=255)
image_id = fields.CharField(max_length=255)
image_data = fields.BinaryField()  # 使用 BinaryField 来存储二进制数据（例如图片）
```

### daily_wife
```python
id = fields.IntField(pk=True, generated=True)
user_id = fields.CharField(max_length=32)
wife_id = fields.CharField(max_length=32)
date = fields.DateField(default=date(2000, 1, 1))
```

### daily_children
```python
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
```
