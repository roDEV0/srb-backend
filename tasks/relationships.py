from datetime import datetime, timedelta, timezone

from aiohttp import ClientSession
from loguru import logger
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from models.relationships.player_relationships import PlayerTownRelationship, PlayerNationRelationship
from requester import post_request, get_request
from models.relationships.player_relationships import PlayerTownRelationship, PlayerNationRelationship
from models.relationships.relationship import PlayerRelationship
from models.base import Player, Town, Nation

logger.add("main.log", format="{time} {level} {message}", rotation="10 MB")

class RelationshipManager:
    def __init__(self) -> None:
        self.priority_queue: list[str] = []
        self.long_queue: list[str] = []

    def get_short_queue(self):
        return self.priority_queue.copy()

    def get_long_queue(self):
        return self.long_queue.copy()

    def add_to_priority_queue(self, relationships: list[str]):
        self.priority_queue.extend(relationships)

    def add_to_long_queue(self, relationships: list[str]):
        self.long_queue.extend(relationships)

    def flush_queue(self):
        self.priority_queue = []

async def check_relationships(session: ClientSession, to_check: list[str]):
    logger.info("Started relationship checks")
    new_town_relationships = []
    player_data = await post_request(session, 'players', to_check)

    player_instances = await Player.filter(uuid__in=to_check)
    player_instance_map = {player.uuid: player for player in player_instances}

    town_instances = await Town.filter(uuid__in=[player['town']['uuid'] for player in player_data if player['town']['uuid']])
    town_instance_map = {town.uuid: town for town in town_instances}

    # Add Citizen Relationships
    new_town_relationships.extend([
        PlayerTownRelationship(
            player=player_instance_map[player['uuid']],
            town=town_instance_map[player['town']['uuid']],
            relationship=PlayerRelationship.CITIZEN
        ) for player in player_data if player['uuid'] in player_instance_map and player['town']['uuid']
    ])

    # Add Mayor Relationships
    new_town_relationships.extend([
        PlayerTownRelationship(
            player=player_instance_map[player['uuid']],
            town=town_instance_map[player['town']['uuid']],
            relationship=PlayerRelationship.MAYOR
        ) for player in player_data if player['status']['isMayor'] and player['uuid'] in player_instance_map
    ])

    new_nation_relationships = []
    nation_instances = await Nation.filter(uuid__in=[player['nation']['uuid'] for player in player_data if player['nation']['uuid']])
    nation_instance_map = {nation.uuid: nation for nation in nation_instances}

    new_nation_relationships.extend([
        PlayerNationRelationship(
            player=player_instance_map[player['uuid']],
            nation=nation_instance_map[player['nation']['uuid']],
            relationship=PlayerRelationship.CITIZEN
        ) for player in player_data if player['uuid'] in player_instance_map and player['nation']['uuid']
    ])

    new_nation_relationships.extend([
        PlayerNationRelationship(
            player=player_instance_map[player['uuid']],
            nation=nation_instance_map[player['nation']['uuid']],
            relationship=PlayerRelationship.KING
        ) for player in player_data if player['status']['isKing'] and player['uuid'] in player_instance_map
    ])

    if not new_town_relationships:
        logger.info("Finished relationship checks with no mew relationships")

    if not new_nation_relationships:
        logger.info("Finished relationship checks with no mew relationships")

    logger.info("Starting relationship transaction with database")
    async with in_transaction():
        try:
            await PlayerTownRelationship.bulk_create(new_town_relationships, ignore_conflicts=True)

            query = Q()

            for rel in new_town_relationships:
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
            ).exclude(query).update(ended=True)
        except Exception:
            pass

    async with in_transaction():
        try:
            logger.debug([relationship.relationship for relationship in new_nation_relationships])
            await PlayerNationRelationship.bulk_create(new_nation_relationships, ignore_conflicts=True)

            query = Q()

            for rel in new_nation_relationships:
                query |= Q(
                    player_id=rel.player_id,
                    nation_id=rel.nation_id,
                    relationship=rel.relationship,
                )

            await PlayerNationRelationship.filter(
                player_id__in=[
                    player_instance_map[uuid].id for uuid in to_check
                    if uuid in player_instance_map
                ]
            ).exclude(query).update(ended=True)
        except Exception as e:
            logger.exception(e)


    logger.info("Finished relationship checks successfully")

async def check_towns(session: ClientSession, to_check: list[str]):
    logger.info("Started town checks")

    player_data = await post_request(session, 'players', to_check)
    town_uuids = list({
        player["town"]["uuid"]
        for player in player_data
        if player["town"]["uuid"]
    })
    town_data = await post_request(session, 'towns', town_uuids) if town_uuids else []

    new_towns = [Town(
        uuid = town['uuid'],
        name = town['name'],
        town_blocks = len(town['coordinates']['townBlocks']),
        created_at=datetime.fromtimestamp(town['timestamps']['registered'] / 1000, tz=timezone.utc),
        gold=town['stats']['balance']
    ) for town in town_data]

    await Town.bulk_create(new_towns, on_conflict=['uuid'], update_fields=['name', 'town_blocks', 'gold'])

    logger.info("Finished town checks successfully")

async def check_nation(session: ClientSession, to_check: list[str]):
    logger.info("Started nation checks")

    player_data = await post_request(session, 'players', to_check)
    nation_uuids = list({
        player["nation"]["uuid"]
        for player in player_data
        if player["nation"]["uuid"]
    })
    nation_data = await post_request(session, 'nations', nation_uuids) if nation_uuids else []

    new_nations = [Nation(
        uuid=nation['uuid'],
        name=nation['name'],
        created_at=datetime.fromtimestamp(nation['timestamps']['registered'] / 1000, tz=timezone.utc),
        gold=nation['stats']['balance']
    ) for nation in nation_data]

    await Nation.bulk_create(new_nations, on_conflict=['uuid'], update_fields=['name', 'gold'])

    logger.info("Finished nation checks")

async def recency_checks(session: ClientSession, manager: RelationshipManager):
    current_queue = manager.priority_queue
    logger.info(f"There are currently {len(current_queue)} players in the queue")
    if current_queue:
        await check_towns(session, current_queue)
        await check_nation(session, current_queue)
        await check_relationships(session, current_queue)

    manager.flush_queue()

