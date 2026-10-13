import os

DATABASE_URL = os.getenv("DATABASE_URL")

TORTOISE_ORM = {
    "connections": {
        "default": DATABASE_URL,
    },
    "apps": {
        "models": {
            "models": ["models.base", "models.events.nation_events", "models.events.player_events", "models.events.town_events", "models.session", "models.relationships.player_relationships"],
            "default_connection": "default",
            "migrations": "migrations",
        },
    },
}