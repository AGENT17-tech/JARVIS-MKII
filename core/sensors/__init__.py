"""
sensors/__init__.py — JARVIS MKIII Sensor Registry
Registers all available sensors with the world state engine.

Usage:
    from sensors import register_all_sensors
    register_all_sensors(world_state)
"""

from world_state import WorldState


def register_all_sensors(ws: WorldState):
    """Register all available sensors with the world state engine."""

    # GitHub — always available (public API, no auth)
    try:
        from sensors.github_sensor import github_sensor
        ws.register_sensor(github_sensor)
        print("[SENSORS] GitHub sensor registered.")
    except Exception as e:
        print(f"[SENSORS] GitHub sensor failed: {e}")

    # Gmail — requires OAuth2 credentials
    try:
        from sensors.gmail_sensor import gmail_sensor
        ws.register_sensor(gmail_sensor)
        print("[SENSORS] Gmail sensor registered.")
    except Exception as e:
        print(f"[SENSORS] Gmail sensor failed: {e}")

    # Google Calendar — requires OAuth2 credentials
    try:
        from sensors.gcal_sensor import gcal_sensor
        ws.register_sensor(gcal_sensor)
        print("[SENSORS] Google Calendar sensor registered.")
    except Exception as e:
        print(f"[SENSORS] GCal sensor failed: {e}")

    # BUC Portal — requires credentials in vault
    try:
        from sensors.buc_sensor import buc_sensor
        ws.register_sensor(buc_sensor)
        print("[SENSORS] BUC sensor registered.")
    except Exception as e:
        print(f"[SENSORS] BUC sensor failed: {e}")

    # Discord — requires bot token in vault
    try:
        from sensors.discord_sensor import discord_sensor
        ws.register_sensor(discord_sensor)
        print("[SENSORS] Discord sensor registered.")
    except Exception as e:
        print(f"[SENSORS] Discord sensor failed: {e}")

    print(f"[SENSORS] {len(ws._sensors)} sensor(s) active.")
