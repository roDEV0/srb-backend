from tortoise import fields
from .event import Event

class UsernameChangeEvent(Event):
    player = fields.ForeignKey("models.Player", on_delete=fields.CASCADE, related_name="previous_usernames")
    old_username = fields.CharField(max_length=64, null=True)
    new_username = fields.CharField(max_length=64, null=False)

    class Meta:
        table = "username_change_event"

class InactiveKickEvent(Event):
    player = fields.ForeignKey("models.Player", on_delete=fields.CASCADE, related_name="inactive_kicks")
    last_online = fields.DatetimeField(null=False, auto_now_add=False)

    class Meta:
        table = "inactive_kick_event"