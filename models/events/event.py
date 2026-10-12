from tortoise.models import Model
from tortoise import fields

class Event(Model):
    id = fields.IntField(pk=True)
    time = fields.DatetimeField(auto_now_add=True)

    class Meta:
        abstract = True
        schema = "events"