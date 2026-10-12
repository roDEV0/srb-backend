from tortoise import fields
from tortoise.migrations.constraints import UniqueConstraint
from tortoise.models import Model

from models.relationships import relationship
from models.relationships.relationship import PlayerRelationship


class PlayerTownRelationship(Model):
    id = fields.IntField(pk=True)
    player = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="town_relationships")
    town = fields.ForeignKeyField("models.Town", on_delete=fields.CASCADE, related_name="player_relationships")
    relationship = fields.CharEnumField(enum_type=PlayerRelationship, default=PlayerRelationship.CITIZEN)
    established = fields.DatetimeField(auto_now_add=True)
    ended = fields.BooleanField(default=False)

    class Meta:
        table = "player_town_relationships"
        constraints = [
            UniqueConstraint(
                fields=("player", "town", "relationship"),
                condition="NOT ended",
                name="player_town_relationships_unique"
            )
        ]

class PlayerNationRelationship(Model):
    id = fields.IntField(pk=True)
    player = fields.ForeignKeyField("models.Player", on_delete=fields.CASCADE, related_name="nation_relationships")
    nation = fields.ForeignKeyField("models.Nation", on_delete=fields.CASCADE, related_name="player_relationships")
    relationship = fields.CharEnumField(enum_type=PlayerRelationship, default=PlayerRelationship.CITIZEN)
    established = fields.DatetimeField(auto_now_add=True)
    ended = fields.BooleanField(default=False)

    class Meta:
        table = "player_nation_relationships"
        constraints = [
            UniqueConstraint(
                fields=("player", "nation", "relationship"),
                condition="NOT ended",
                name="player_nation_relationships_unique"
            )
        ]