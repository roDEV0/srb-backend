from tortoise import fields
from .event import Event
from .reason import EventReason

class TownCreatedEvent(Event):
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="creation_event")
    mayor = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="created_towns")

    class Meta:
        table = "town_created_event"

class TownDeletedEvent(Event):
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="deletion_event")
    mayor = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="deleted_towns")

    class Meta:
        table = "town_deleted_event"

class CitizenLeaveEvent(Event):
    player = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="previous_towns")
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="previous_citizens")
    reason = fields.CharEnumField(enum_type=EventReason, default=EventReason.LEFT)

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
    reason = fields.CharEnumField(enum_type=EventReason, default=EventReason.TRANSFERRED)

    class Meta:
        table = "mayor_change_event"

class TownCollapseEvent(Event):
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="collapsed")
    mayor = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="ruined_towns")

    class Meta:
        table = "town_collapse_event"

class TownReclaimedEvent(Event):
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="reclaimed")
    mayor = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="reclaimed_towns")

    class Meta:
        table = "town_reclaimed_event"

class TownMergedEvent(Event):
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="contains")
    merged_in = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="merged_in")

    class Meta:
        table = "town_merged_event"