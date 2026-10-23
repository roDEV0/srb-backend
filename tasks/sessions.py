from datetime import datetime, timezone
from dataclasses import dataclass
import aiohttp
from loguru import logger

from models.base import Player
from models.session import ActiveSession, Session
from requester import post_request, get_request, position_request
from tasks.relationships import RelationshipManager

logger.add("main.log", format="{time} {level} {message}", rotation="10 MB")

class SessionManager:
    def __init__(self) -> None:
        self.active: dict[str, LocalActiveSession] = {}

    def end_session(self, uuid: str):
        session = self.active.pop(uuid, None)
        return session.end() if session else None

@dataclass
class LocalActiveSession:
    player_uuid: str
    start_time: datetime
    positions: list[dict]
    database_instance: ActiveSession

    @classmethod
    def from_active_session(cls, session: ActiveSession):
        return cls(
            player_uuid=session.uuid,
            start_time=session.start_time,
            positions=list(session.positions),
            database_instance=session,
        )

    def append_position(self, position: dict) -> None:
        self.positions.append(position)

    def end(self) -> dict:
        end_time = datetime.now(timezone.utc)

        return {
            "database_object": self.database_instance,
            "positions": self.positions,
            "start_time": self.start_time,
            "end_time": end_time,
        }

async def handle_new_players(session: aiohttp.ClientSession, new: list[str]):
    if not new:
        return []
    logger.info(f"{len(new)} new players have been noticed")
    data = await post_request(session, 'players', new)
    new_instances = [Player(
        uuid=player['uuid'],
        name=player['name'],
        playtime=None,
        joined=datetime.fromtimestamp(player['timestamps']['registered'] / 1000, tz=timezone.utc),
        gold=player['stats']['balance']
    ) for player in data]
    await Player.bulk_create(new_instances)

    return await Player.filter(uuid__in=[player.uuid for player in new_instances])

def format_uuid(uuid: str) -> str:
    if "-" in uuid:
        return uuid
    return f"{uuid[:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:]}"

async def compare_active_sessions(session: aiohttp.ClientSession, manager: SessionManager, relationships: RelationshipManager):
    logger.info("Starting the compare active sessions process")
    uuids = set(item['uuid'] for item in (await get_request(session, 'online'))['players'])

    positions = await position_request(session)
    position_map = {format_uuid(player['uuid']): {'x': player['x'], 'y': player['y'], 'z': player['z']} for player in positions['players'] if player['world'] == 'minecraft_overworld'}

    # New Players
    new_sessions = []
    new_uuids = uuids - set(manager.active)
    existing_sessions = await ActiveSession.filter(uuid__in=new_uuids)
    existing_map = {active_instance.uuid: active_instance for active_instance in existing_sessions}
    for uuid in new_uuids:
        if uuid not in existing_map:
            new_instance = ActiveSession(
                uuid=uuid,
                start_time=datetime.now(timezone.utc)
            )
            new_sessions.append(new_instance)
        else:
            new_instance = existing_map[uuid]
        manager.active[uuid] = LocalActiveSession.from_active_session(new_instance)
    await ActiveSession.bulk_create(new_sessions)

    # Lost Players
    lost_uuids = set(manager.active) - uuids
    lost_instances = await Player.filter(uuid__in=lost_uuids)
    lost_instances_by_uuid = {instance.uuid: instance for instance in lost_instances}

    for instance in await handle_new_players(session, [uuid for uuid in lost_uuids if uuid not in lost_instances_by_uuid]):
        lost_instances_by_uuid[instance.uuid] = instance

    popped_data_by_uuid = {uuid: manager.end_session(uuid) for uuid in lost_instances_by_uuid if uuid in manager.active}

    new_session_instances = []

    for uuid, player in lost_instances_by_uuid.items():
        session_data = popped_data_by_uuid[uuid]

        new_session_instances.append(
            Session(
                player=player,
                start_time=session_data["start_time"],
                end_time=session_data["end_time"],
                playtime=session_data["end_time"] - session_data["start_time"],
                positions=session_data["positions"],
                gold=player.gold,
            )
        )

    await Session.bulk_create(new_session_instances)

    for local in manager.active.values():
        if local.player_uuid in position_map:
            local.append_position(position_map[local.player_uuid])

    logger.info("Completed the compare active sessions process")

    relationships.add_to_queue([uuid for uuid in uuids if uuid not in relationships.queue])