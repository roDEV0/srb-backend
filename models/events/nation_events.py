from tortoise import fields
from .event import Event
from .reason import EventReason

class NationMergedEvent(Event):
    nation = fields.ForeignKeyField("models.Nation", on_delete=fields.CASCADE, related_name="contains")
    merged_in = fields.ForeignKeyField("models.Nation", on_delete=fields.CASCADE, related_name="merged_in")

    class Meta:
        table = "nation_merged_event"

class NationCreatedEvent(Event):
    nation = fields.ForeignKeyField("models.Nation", on_delete=fields.CASCADE, related_name="created")
    king = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="created_nations")
    capitol = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="created_nations")

    class Meta:
        table = "nation_created_event"

class NationDeletedEvent(Event):
    nation = fields.ForeignKeyField("models.Nation", on_delete=fields.CASCADE, related_name="deleted")
    king = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="deleted_nations")
    capitol = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="deleted_nations")

    class Meta:
        table = "nation_deleted_event"

class TownLeaveEvent(Event):
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="previous_nations")
    nation = fields.ForeignKeyField("models.Nation", on_delete=fields.CASCADE, related_name="previous_towns")
    reason = fields.CharEnumField(enum_type=EventReason, default=EventReason.LEFT)

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
    reason = fields.CharEnumField(enum_type=EventReason, default=EventReason.TRANSFERRED)

    class Meta:
        table = "king_change_event"

class NationCollapseEvent(Event):
    nation = fields.ForeignKeyField("models.Nation", on_delete=fields.CASCADE, related_name="collapsed")

    class Meta:
        table = "nation_collapse_event"