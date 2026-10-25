from datetime import datetime, timezone, timedelta

from aiohttp import ClientSession

from models.base import Player
from requester import post_request
from models.events.player_events import InactiveKickEvent
from tasks.relationships import RelationshipManager


async def refresh_queue(manager: RelationshipManager):
    active_players = await Player.filter(active=True).all()
    manager.add_to_long_queue([player.uuid for player in active_players if player.uuid not in manager.get_long_queue()])

async def check_validity(session: ClientSession, manager: RelationshipManager):
    to_check = manager.get_long_queue()
    player_data = await post_request(session, 'players', to_check)

    if not player_data:
        return

    instances = await Player.filter(uuid__in=to_check).all()
    instances_map = {player.uuid: player for player in instances}

    new_inactive_events = []

    for player in player_data:
        if (datetime.now(timezone.utc).timestamp() - (player['timestamps']['lastOnline'] / 1000)) > timedelta(days=30).total_seconds():
            new_inactive_events.append(InactiveKickEvent(player=instances_map[player['uuid']], last_online=datetime.fromtimestamp(player['timestamps']['lastOnline'] / 1000, tz=timezone.utc)))
            instances_map[player['uuid']].active = False

    await Player.bulk_update(new_inactive_events, fields=['active']) if new_inactive_events else None
    await InactiveKickEvent.bulk_create(new_inactive_events) if new_inactive_events else None