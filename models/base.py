from tortoise.models import Model
from tortoise import fields

class Player(Model):
    id = fields.IntField(primary_key=True)
    uuid = fields.data.CharField(max_length=64, unique=True, null=False)
    name = fields.CharField(max_length=64, null=False)
    playtime = fields.TimeDeltaField(null=True)
    joined = fields.DatetimeField(null=True)
    gold = fields.IntField(null=True)

class Town(Model):
    id = fields.IntField(pk=True)
    uuid = fields.data.CharField(max_length=64, unique=True)
    name = fields.CharField(max_length=64, null=False)
    town_blocks = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    gold = fields.IntField(null=True)


class Nation(Model):
    id = fields.IntField(pk=True)
    uuid = fields.CharField(max_length=64, unique=True)
    name = fields.CharField(max_length=64, null=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    gold = fields.IntField(null=True)
