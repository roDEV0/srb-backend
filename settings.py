import os

TORTOISE_ORM = {
    "connections": {
        "default": os.getenv("DATABASE_URL"),
    },
    "apps": {
        "models": {
            "models": ["models.base", "models.events.nation_events", "models.events.player_events", "models.events.town_events", "models.session"],
            "default_connection": "default",
            "migrations": "migrations",
        },
    },
}