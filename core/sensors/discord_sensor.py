"""
discord_sensor.py — JARVIS MKIII Discord Sensor
Monitors mentions and DMs via Discord bot.

Setup:
    1. Go to discord.com/developers/applications
    2. Create a new application → Bot → Copy token
    3. Run: python3 vault.py store DISCORD_TOKEN your_token_here
    4. Invite bot to your server with Read Messages permission
"""

import asyncio
import os
from vault import vault


class DiscordSensor:
    def __init__(self):
        self._available  = False
        self._unread     = 0
        self._mentions   = 0
        self._client     = None
        print("[DISCORD SENSOR] Initialized.")

    async def _connect(self):
        """Connect Discord bot in background."""
        token = vault.get("DISCORD_TOKEN")
        if not token:
            print("[DISCORD SENSOR] No token in vault — skipping.")
            return

        try:
            import discord

            intents          = discord.Intents.default()
            intents.messages = True
            intents.message_content = True

            self._client = discord.Client(intents=intents)

            @self._client.event
            async def on_ready():
                self._available = True
                print(f"[DISCORD SENSOR] Connected as {self._client.user}")

            @self._client.event
            async def on_message(message):
                if message.author == self._client.user:
                    return
                # Count mentions
                if self._client.user in message.mentions:
                    self._mentions += 1
                self._unread += 1

            # Run in background
            asyncio.create_task(self._client.start(token))

        except Exception as e:
            print(f"[DISCORD SENSOR] Connection error: {e}")

    async def read(self) -> dict:
        if not self._available and not self._client:
            await self._connect()

        result = {
            "discord": {
                "unread_messages": self._unread,
                "mentions":        self._mentions,
            }
        }
        # Reset counters after read
        self._unread   = 0
        self._mentions = 0
        return result


discord_sensor = DiscordSensor()

if __name__ == "__main__":
    async def test():
        print("[TEST] Discord sensor...")
        token = vault.get("DISCORD_TOKEN")
        if not token:
            print("[TEST] No DISCORD_TOKEN in vault.")
            print("       Run: python3 vault.py store DISCORD_TOKEN your_token")
            print("[TEST] Discord skipped — not configured.")
        else:
            result = await discord_sensor.read()
            print(f"Result: {result}")
            print("[TEST] Discord PASS")
    asyncio.run(test())
