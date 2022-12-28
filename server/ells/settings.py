import json

settings = {}


def create_settings():
    global settings

    settings = {"protection": {"type": "none", "key": ""},
                "security": {"bot_timeout": 30}}

    with open("settings.json", "w") as file:
        json.dump(settings, file)


def load_settings():
    global settings

    with open("settings.json", "r") as file:
        settings = json.load(file)


def get_settings():
    global settings
    return settings


def update_settings():
    global settings

    with open("settings.json", "w") as file:
        json.dump(settings, file)
