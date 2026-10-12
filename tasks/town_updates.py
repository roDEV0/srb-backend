from datetime import datetime, timedelta

from aiohttp import ClientSession
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from models.relationships.player_relationships import PlayerTownRelationship, PlayerNationRelationship
from requester import post_request, get_request
from models.relationships.player_relationships import PlayerTownRelationship, PlayerNationRelationship
from models.relationships.relationship import PlayerRelationship
from models.base import Player, Town


class RelationshipManager:
    def __init__(self) -> None:
        self.queue: list[str] = []

    def add_to_queue(self, relationships: list[str]):
        self.queue.extend(relationships)

    def flush_queue(self):
        self.queue = []

async def check_relationships(session: ClientSession, to_check: list[str]):
    print("Started Relationship Checks")
    new_relationships = []
    if not to_check:
        print(to_check)
        print("Finished Relationship Checks")
        return
    player_data = await post_request(session, 'players', to_check)

    player_instances = await Player.filter(uuid__in=to_check)
    player_instance_map = {player.uuid: player for player in player_instances}

    town_instances = await Town.filter(uuid__in=[player['town']['uuid'] for player in player_data if player['town']['uuid']])
    town_instance_map = {town.uuid: town for town in town_instances}

    # Add Citizen Relationships
    new_relationships.extend([
        PlayerTownRelationship(
            player=player_instance_map[player['uuid']],
            town=town_instance_map[player['town']['uuid']],
            relationship=PlayerRelationship.CITIZEN
        ) for player in player_data if player['uuid'] in player_instance_map
    ])

    # Add Mayor Relationships
    new_relationships.extend([
        PlayerTownRelationship(
            player=player_instance_map[player['uuid']],
            town=town_instance_map[player['town']['uuid']],
            relationship=PlayerRelationship.MAYOR
        ) for player in player_data if player['status']['isMayor'] and player['uuid'] in player_instance_map
    ])

    if not new_relationships:
        print("Finished Relationship Checks")
        return

    print("Starting Transaction")
    async with in_transaction():
        try:
            await PlayerTownRelationship.bulk_create(new_relationships, ignore_conflicts=True)

            query = Q()

            for rel in new_relationships:
                query |= Q(
                    player_id=rel.player_id,
                    town_id=rel.town_id,
                    relationship=rel.relationship,
                )

            await PlayerTownRelationship.filter(
                player_id__in=[
                    player_instance_map[uuid].id for uuid in to_check
                    if uuid in player_instance_map
                ]
            ).exclude(query).update(is_valid=False)
        except Exception:
            pass

    print("Finished Relationship Checks")