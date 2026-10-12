TORTOISE_ORM = {
    "connections": {
        "default": "postgresql://neondb_owner:npg_6tE8cTbGUkdn@ep-autumn-grass-b4r7xlgy-pooler.c-6.us-east-2.aws.neon.tech/neondb",
    },
    "apps": {
        "models": {
            "models": ["models.base", "models.events.nation_events", "models.events.player_events", "models.events.town_events", "models.session"],
            "default_connection": "default",
            "migrations": "migrations",
        },
    },
}