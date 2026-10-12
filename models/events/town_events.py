from tortoise import fields
from .event import Event

class CitizenLeaveEvent(Event):
    player = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="previous_towns")
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="previous_citizens")
    reason = fields.CharField(max_length=10, null=True)

    class Meta:
        table = "citizen_leave_event"

class CitizenJoinEvent(Event):
    player = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="joined_towns")
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="citizen_history")

    class Meta:
        table = "citizen_join_event"

class TownNameChangeEvent(Event):
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="previous_names")
    old_name = fields.CharField(max_length=64, null=True)
    new_name = fields.CharField(max_length=64, null=True)

    class Meta:
        table = "town_name_change_event"

class MayorChangeEvent(Event):
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="previous_mayorship")
    old_mayor = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="previous_mayorship")
    new_mayor = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="mayor_history")
    reason = fields.CharField(max_length=10, null=True)

    class Meta:
        table = "mayor_change_event"

class TownCollapseEvent(Event):
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="collapsed")

    class Meta:
        table = "town_collapse_event"