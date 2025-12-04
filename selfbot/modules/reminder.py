import asyncio
import datetime
import re
from pyrogram import filters
from pyrogram.types import Message
from selfbot import listener
from selfbot.module import Module

class Reminder(Module):
    name = "Reminder"
    cmds = [
        "!remind {time} {text}",
        "!remindme {time} {text}",
        "!sremind {time} {text}",
        "!sremindme {time} {text}"
    ]
    desc = {
        "time": "Format waktu (HH:MM, YYYY-MM-DD_HH:MM, atau relatif N[smhdwy])",
        "text": "Pesan yang akan dikirim saat waktunya tiba"
    }

    def parse_time(self, time_str: str) -> float:
        """
        Convert time string into seconds delay.
        Supported formats:
        - HH:MM
        - YYYY-MM-DD_HH:MM
        - N[smhdwy] (relative)
        - Compound relative (e.g. 1h30m)
        """
        now = datetime.datetime.now()

        # Format HH:MM
        if re.match(r"^\d{2}:\d{2}$", time_str):
            hour, minute = map(int, time_str.split(":"))
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target < now:
                target += datetime.timedelta(days=1)
            return (target - now).total_seconds()

        # Format YYYY-MM-DD_HH:MM
        if re.match(r"^\d{4}-\d{2}-\d{2}_\d{2}:\d{2}$", time_str):
            date_part, hm = time_str.split("_")
            year, month, day = map(int, date_part.split("-"))
            hour, minute = map(int, hm.split(":"))
            target = datetime.datetime(year, month, day, hour, minute)
            return (target - now).total_seconds()

        # Relative format N[smhdwy]...
        units = {"s":1, "m":60, "h":3600, "d":86400, "w":604800, "y":31536000}
        matches = re.findall(r"(\d+)([smhdwy])", time_str)
        if matches:
            total = sum(int(num) * units[unit] for num, unit in matches)
            return total

        raise ValueError("Invalid time format")

    async def set_reminder(self, event: Message, time_str: str, text: str, silent: bool, self_only: bool):
        try:
            delay = self.parse_time(time_str)
        except Exception as e:
            await event.edit_text(f"❌ Format waktu salah: {e}")
            return

        if silent:
            await event.delete()
        else:
            await event.edit_text(f"⏰ Reminder set untuk {time_str}")

        async def remind_task():
            await asyncio.sleep(delay)
            if self_only:
                await event.client.send_message("me", f"🔔 Reminder: {text}")
            else:
                await event.reply(f"🔔 Reminder: {text}")

        asyncio.create_task(remind_task())

    @listener.handler(filters.regex(r"^!remind (\S+) (.+)$"))
    async def remind(self, event: Message):
        time_str, text = event.matches[0].group(1), event.matches[0].group(2)
        await self.set_reminder(event, time_str, text, silent=False, self_only=False)

    @listener.handler(filters.regex(r"^!remindme (\S+) (.+)$"))
    async def remindme(self, event: Message):
        time_str, text = event.matches[0].group(1), event.matches[0].group(2)
        await self.set_reminder(event, time_str, text, silent=False, self_only=True)

    @listener.handler(filters.regex(r"^!sremind (\S+) (.+)$"))
    async def sremind(self, event: Message):
        time_str, text = event.matches[0].group(1), event.matches[0].group(2)
        await self.set_reminder(event, time_str, text, silent=True, self_only=False)

    @listener.handler(filters.regex(r"^!sremindme (\S+) (.+)$"))
    async def sremindme(self, event: Message):
        time_str, text = event.matches[0].group(1), event.matches[0].group(2)
        await self.set_reminder(event, time_str, text, silent=True, self_only=True)
