import asyncio
import os
from datetime import datetime, timezone, timedelta
import json
import aiohttp
from httpx_sse import aconnect_sse, ServerSentEvent, SSEError
from models.events.town_events import *
from models.events.nation_events import *
from models.base import *
import httpx

from requester import post_request

headers = {
    "Authorization": f"Bearer {os.getenv('API_KEY')}"
}

SSE_URL = "https://api.earthmc.net/v4/events?listen=TownRenamed,TownCreated,TownDeleted,TownMayorChanged,TownMerged,TownRuined,TownReclaimed,NationCreated,NationDeleted,NationRenamed,NationKingChanged,NationMerged"
MAX_BACKOFF = 60

async def setup_sse(session: aiohttp.ClientSession):
    timeout = httpx.Timeout(timeout=5.0, read=None)

    async with httpx.AsyncClient(timeout=timeout) as client:
        while True:
            async with aconnect_sse(client, "GET", url=SSE_URL, headers=headers) as src:
                src.response.raise_for_status()
                async for sse in src.aiter_sse():
                    print(sse)
                    await handle_event(sse, session)

# TODO: Refactor

async def handle_unknown_item(session: aiohttp.ClientSession, category: str, item: str):
    data = await post_request(session, category, [item])
    if not data:
        return []
    instance = None

    # Update or create is used in case the new instance is somehow made after the previous check
    if category == 'players':
        instance = await Player.update_or_create(
            uuid=data[0]['uuid'],
            name=data[0]['name'],
            playtime=None,
            joined=datetime.fromtimestamp(data[0]['timestamps']['registered'] / 1000, tz=timezone.utc),
            gold=data[0]['stats']['balance']
        )
    if category == 'towns':
        instance = await Town.update_or_create(
            uuid=data[0]['uuid'],
            name=data[0]['name'],
            town_blocks=len(data[0]['coordinates']['townBlocks']),
            created_at=datetime.fromtimestamp(data[0]['timestamps']['registered'] / 1000, tz=timezone.utc),
            gold=data[0]['stats']['balance']
        )
    if category == 'nations':
        instance = await Nation.update_or_create(
            uuid=data[0]['uuid'],
            name=data[0]['name'],
            created_at=datetime.fromtimestamp(data[0]['timestamps']['registered'] / 1000, tz=timezone.utc),
            gold=data[0]['stats']['balance']
        )

    return instance[0] if instance else []

async def handle_event(event: ServerSentEvent, session: aiohttp.ClientSession):
    data = json.loads(event.data)

    # NATIONS

    if event.event == "NationRenamed":
        nation = await Nation.get_or_none(uuid=data['nation']['uuid'])

        nation = await handle_unknown_item(session, 'nations', data['nation']['uuid']) if not nation else nation

        await NationNameChangeEvent.create(
            nation=nation,
            old_name=data['oldName'],
            new_name=data['nation']['name']
        ) if nation else None

    if event.event == "NationKingChanged":
        nation, old_king, new_king = await asyncio.gather(
            Nation.get_or_none(uuid=data["nation"]["uuid"]),
            Player.get_or_none(uuid=data["oldKing"]["uuid"]),
            Player.get_or_none(uuid=data["newKing"]["uuid"]),
        )

        nation = nation if nation else (await handle_unknown_item(session, 'nations', data["nation"]["uuid"]))
        old_king = old_king if old_king else (await handle_unknown_item(session, 'players', data["oldKing"]["uuid"]))
        new_king = new_king if new_king else (await handle_unknown_item(session, 'players', data["newKing"]["uuid"]))

        if not nation or not old_king or not new_king:
            return

        old_king_data = await post_request(session, 'players', [old_king.uuid])
        reason = EventReason.AFK if (datetime.now(timezone.utc).timestamp() - (old_king_data[0]['timestamps']['lastOnline'] / 1000)) > timedelta(days=30).total_seconds() else EventReason.TRANSFERRED
        await KingChangeEvent.create(
            nation=nation,
            old_king=old_king,
            new_king=new_king,
            reason=reason
        )

    if event.event == "NationMerged":
        nation, old_nation = await asyncio.gather(
            Nation.get_or_none(uuid=data["remainingNation"]["uuid"]),
            Nation.get_or_none(uuid=data["oldNation"]["uuid"]),
        )

        nation = nation if nation else (await handle_unknown_item(session, 'nations', data["remainingNation"]["uuid"]))
        old_nation = old_nation if old_nation else (await handle_unknown_item(session, 'nations', data["oldNation"]["uuid"]))

        await NationMergedEvent.create(
            nation=nation,
            merged_in=old_nation
        ) if nation and old_nation else None

    if event.event == "NationCreated":
        nation, king, capitol = await asyncio.gather(
            Nation.get_or_none(uuid=data["nation"]["uuid"]),
            Player.get_or_none(uuid=data["king"]["uuid"]),
            Town.get_or_none(uuid=data["capitol"]["uuid"]),
        )

        nation = nation if nation else (await handle_unknown_item(session, 'nations', data["nation"]["uuid"]))
        king = king if king else (await handle_unknown_item(session, 'players', data["king"]["uuid"]))
        capitol = capitol if capitol else (await handle_unknown_item(session, 'towns', data["capitol"]["uuid"]))

        await NationCreatedEvent.create(
            nation=nation if nation else (await handle_unknown_item(session, 'nations', data["nation"]["uuid"])),
            king=king if king else (await handle_unknown_item(session, 'players', data["king"]["uuid"])),
            capitol=capitol if capitol else (await handle_unknown_item(session, 'towns', data["capitol"]["uuid"]))
        ) if nation and king and capitol else None

    if event.event == "NationDeleted":
        nation, king, capitol = await asyncio.gather(
            Nation.get_or_none(uuid=data["nation"]["uuid"]),
            Player.get_or_none(uuid=data["king"]["uuid"]),
            Town.get_or_none(uuid=data["capitol"]["uuid"]),
        )

        nation = nation if nation else (await handle_unknown_item(session, 'nations', data["nation"]["uuid"]))
        king = king if king else (await handle_unknown_item(session, 'players', data["king"]["uuid"]))
        capitol = capitol if capitol else (await handle_unknown_item(session, 'towns', data["capitol"]["uuid"]))

        await NationDeletedEvent.create(
            nation=nation if nation else (await handle_unknown_item(session, 'nations', data["nation"]["uuid"])),
            king=king if king else (await handle_unknown_item(session, 'players', data["king"]["uuid"])),
            capitol=capitol if capitol else (await handle_unknown_item(session, 'towns', data["capitol"]["uuid"]))
        ) if nation and king and capitol else None

    # TOWNS

    if event.event == "TownRenamed":
        town = await Town.get_or_none(uuid=data['town']['uuid'])

        town = town if town else (await handle_unknown_item(session, 'towns', data['town']['uuid']))

        await TownNameChangeEvent.create(
            town=town,
            old_name=data['oldName'],
            new_name=data['town']['name']
        ) if town else None

    if event.event == "TownMayorChanged":
        town, new_mayor, old_mayor = await asyncio.gather(
            Town.get_or_none(uuid=data["town"]["uuid"]),
            Player.get_or_none(uuid=data["newMayor"]["uuid"]),
            Player.get_or_none(uuid=data["oldMayor"]["uuid"]),
        )

        town = town if town else (await handle_unknown_item(session, 'towns', data["town"]["uuid"]))
        new_mayor = new_mayor if new_mayor else (await handle_unknown_item(session, 'players', data["newMayor"]["uuid"]))
        old_mayor = old_mayor if old_mayor else (await handle_unknown_item(session, 'players', data["oldMayor"]["uuid"]))

        if not old_mayor or not new_mayor or not town:
            return

        old_mayor_data = await post_request(session, 'players', [old_mayor.uuid])
        reason = EventReason.AFK if (datetime.now(timezone.utc).timestamp() - (old_mayor_data[0]['timestamps']['lastOnline'] / 1000)) > timedelta(days=30).total_seconds() else EventReason.TRANSFERRED
        await MayorChangeEvent.create(
            town=town if town else (await handle_unknown_item(session, 'towns', data["town"]["uuid"])),
            old_mayor=old_mayor,
            new_mayor=new_mayor if new_mayor else (await handle_unknown_item(session, 'players', data["newMayor"]["uuid"])),
            reason=reason
        )

    if event.event == "TownMerged":
        town, merged_in = await asyncio.gather(
            Town.get_or_none(uuid=data["remainingTown"]["uuid"]),
            Town.get_or_none(uuid=data["oldTown"]["uuid"]),
        )

        town = town if town else (await handle_unknown_item(session, 'towns', data["remainingTown"]["uuid"]))
        merged_in = merged_in if merged_in else (await handle_unknown_item(session, 'towns', data["oldTown"]["uuid"]))

        await TownMergedEvent.create(
            town=town,
            merged_in=merged_in
        ) if town and merged_in else None

    if event.event == "TownCreated":
        town = await Town.get_or_none(uuid=data['town']['uuid'])
        mayor = await Player.get_or_none(uuid=data['mayor']['uuid'])

        town = town if town else (await handle_unknown_item(session, 'towns', data["town"]["uuid"]))
        mayor = mayor if mayor else (await handle_unknown_item(session, 'players', data["town"]["uuid"]))

        await TownCreatedEvent.create(
            town=town,
            mayor=mayor
        ) if town and mayor else None

    if event.event == "TownDeleted":
        town = await Town.get_or_none(uuid=data['town']['uuid'])
        mayor = await Player.get_or_none(uuid=data['mayor']['uuid'])

        town = town if town else (await handle_unknown_item(session, 'towns', data["town"]["uuid"]))
        mayor = mayor if mayor else (await handle_unknown_item(session, 'players', data["mayor"]["uuid"]))

        await TownDeletedEvent.create(
            town=town,
            mayor=mayor
        ) if town and mayor else None

    if event.event == "TownRuined":
        town = await Town.get_or_none(uuid=data['town']['uuid'])
        mayor = await Player.get_or_none(uuid=data['mayor']['uuid'])

        town = town if town else (await handle_unknown_item(session, 'towns', data["town"]["uuid"]))
        mayor = mayor if mayor else (await handle_unknown_item(session, 'players', data["mayor"]["uuid"]))

        await TownCollapseEvent.create(
            town=town,
            mayor=mayor if mayor else (await handle_unknown_item(session, 'players', data["mayor"]["uuid"]))
        ) if town and mayor else None

    if event.event == "TownReclaimed":
        town = await Town.get_or_none(uuid=data['town']['uuid'])
        mayor = await Player.get_or_none(uuid=data['mayor']['uuid'])

        town = town if town else (await handle_unknown_item(session, 'towns', data["town"]["uuid"]))
        mayor = mayor if mayor else (await handle_unknown_item(session, 'players', data["mayor"]["uuid"]))

        await TownReclaimedEvent.create(
            town=town,
            mayor=mayor
        ) if town and mayor else None