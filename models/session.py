from tortoise.models import Model
from tortoise import fields

class Session(Model):
    id = fields.IntField(pk=True)
    player = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="session")
    start_time = fields.DatetimeField(auto_now_add=True)
    end_time = fields.DatetimeField(auto_now_add=True)
    playtime = fields.TimeDeltaField(null=True)
    positions = fields.JSONField(default=[])
    gold = fields.IntField(default=0)

    class Meta:
        table = "sessions"

class ActiveSession(Model):
    id = fields.IntField(pk=True)
    uuid = fields.CharField(max_length=64, unique=True)
    positions = fields.JSONField(default=[])
    start_time = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "active_sessions"