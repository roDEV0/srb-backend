from tortoise import fields
from .event import Event

class TownLeaveEvent(Event):
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="previous_nations")
    nation = fields.ForeignKeyField("models.Nation", on_delete=fields.CASCADE, related_name="previous_towns")
    reason = fields.CharField(max_length=10, null=True)

    class Meta:
        table = "town_leave_event"

class TownJoinEvent(Event):
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="joined_nations")
    nation = fields.ForeignKeyField("models.Nation", on_delete=fields.CASCADE, related_name="town_history")

    class Meta:
        table = "town_join_event"

class NationNameChangeEvent(Event):
    nation = fields.ForeignKeyField("models.Nation", on_delete=fields.CASCADE, related_name="previous_names")
    old_name = fields.CharField(max_length=64, null=True)
    new_name = fields.CharField(max_length=64, null=True)

    class Meta:
        table = "nation_name_change_event"

class KingChangeEvent(Event):
    nation = fields.ForeignKeyField("models.Nation", on_delete=fields.CASCADE, related_name="previous_kingship")
    old_king = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="previous_kingship")
    new_king = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="king_history")
    reason = fields.CharField(max_length=10, null=True)

    class Meta:
        table = "king_change_event"

class NationCollapseEvent(Event):
    nation = fields.ForeignKeyField("models.Nation", on_delete=fields.CASCADE, related_name="collapsed")

    class Meta:
        table = "nation_collapse_event"