"""DataUpdateCoordinator for VicoHome."""

import aiohttp
import logging
from datetime import datetime, timezone, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN, DEFAULT_POLLING_INTERVAL,
    CONF_EMAIL, CONF_PASSWORD, CONF_REGION, CONF_POLLING_INTERVAL,
    CONF_NOTIFICATIONS, CONF_TELEGRAM_BOT, CONF_TELEGRAM_CHAT,
)

_LOGGER = logging.getLogger(__name__)


class VicoHomeCoordinator(DataUpdateCoordinator):
    """VicoHome data coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.entry = entry
        self.email = entry.data[CONF_EMAIL]
        self.password = entry.data[CONF_PASSWORD]
        self.region = entry.data.get(CONF_REGION, "eu")
        self.interval = entry.data.get(CONF_POLLING_INTERVAL, DEFAULT_POLLING_INTERVAL)

        # Runtime-editable options
        opts = entry.options or {}
        self.notifications_enabled = opts.get(CONF_NOTIFICATIONS, False)
        self.telegram_bot_token = opts.get(CONF_TELEGRAM_BOT, "")
        self.telegram_chat_id = opts.get(CONF_TELEGRAM_CHAT, "")

        self.base_url = f"https://api-{self.region}.vicohome.io"
        self._token: str | None = None
        self._last_notified_trace_id: str | None = None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.interval),
        )

    async def _async_update_data(self):
        """Fetch events from VicoHome API."""
        if not self._token:
            await self._async_login()

        events = await self._async_fetch_events()
        now = datetime.now(timezone.utc)

        # Send Telegram notification for new events
        if events and self.notifications_enabled and self.telegram_bot_token and self.telegram_chat_id:
            latest = events[0]
            trace_id = latest.get("traceId")
            if trace_id and trace_id != self._last_notified_trace_id:
                self._last_notified_trace_id = trace_id
                await self._async_send_telegram(latest)

        return {
            "events": events,
            "last_update": now,
            "event_count": len(events),
        }

    async def _async_login(self) -> None:
        """Login and get token."""
        payload = {
            "email": self.email,
            "password": self.password,
            "loginType": 0,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/account/login",
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                if data.get("result") != 0:
                    raise UpdateFailed(f"Login failed: {data.get('msg', 'unknown error')}")
                self._token = data["data"]["token"]["token"]

    async def _async_fetch_events(self) -> list:
        """Fetch recent events."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(hours=1)
        payload = {
            "startTimestamp": str(int(start.timestamp())),
            "endTimestamp": str(int(now.timestamp())),
            "language": "de",
            "countryNo": "DE" if self.region == "eu" else "US",
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/library/newselectlibrary",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": self._token,
                },
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                if data.get("result") != 0:
                    self._token = None
                    raise UpdateFailed(f"Event fetch failed: {data.get('msg')}")
                return data.get("data", {}).get("list", [])

    async def _async_send_telegram(self, event: dict) -> None:
        """Send Telegram notification for a new event."""
        device_name = event.get("deviceName", "unbekannt")
        ts_raw = event.get("timestamp")
        try:
            from datetime import datetime, timezone
            ts_int = int(ts_raw)
            ts_dt = datetime.fromtimestamp(ts_int, tz=timezone.utc).astimezone()
            ts_str = ts_dt.strftime("%d.%m.%Y, %H:%M:%S")
        except Exception:
            ts_str = str(ts_raw)

        trace_id = event.get("traceId", "n/a")
        image_url = event.get("imageUrl", "")
        video_url = event.get("videoUrl", "")

        msg = (
            f"🎥 *VicoHome Bewegung erkannt!*\n\n"
            f"📷 Gerät: {device_name}\n"
            f"⏰ Zeit: {ts_str}\n"
            f"🆔 Trace: `{trace_id}`"
        )

        await self._async_send_telegram_text(msg)

        # Send image directly as photo if available
        if image_url:
            await self._async_send_telegram_photo(image_url, f"VicoHome – {device_name}")

        # Send video as upload (download to memory + post as FormData) – no disk cache
        if video_url:
            await self._async_send_telegram_video(video_url, f"VicoHome – {device_name}")

    async def _async_send_telegram_text(self, text: str) -> None:
        """Send text message via Telegram Bot API."""
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    result = await resp.json()
                    if not result.get("ok"):
                        _LOGGER.error("Telegram text error: %s", result.get("description"))
        except Exception as err:
            _LOGGER.error("Telegram text failed: %s", err)

    async def _async_send_telegram_photo(self, photo_url: str, caption: str) -> None:
        """Send photo directly via Telegram Bot API."""
        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendPhoto"
        payload = {
            "chat_id": self.telegram_chat_id,
            "photo": photo_url,
            "caption": caption,
            "parse_mode": "Markdown",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    result = await resp.json()
                    if not result.get("ok"):
                        _LOGGER.warning("Telegram photo error: %s", result.get("description"))
        except Exception as err:
            _LOGGER.error("Telegram photo failed: %s", err)

    async def _async_send_telegram_video(self, m3u8_url: str, caption: str) -> None:
        """Download M3U8 stream, convert to MP4 via ffmpeg, upload Telegram sendVideo, then clean up."""
        from pathlib import Path
        import asyncio
        import uuid

        tmp_path = Path(f"/tmp/vicohome_{uuid.uuid4().hex[:8]}.mp4")

        try:
            # 1) ffmpeg: M3U8 → MP4
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-y", "-fflags", "+discardcorrupt",
                "-i", m3u8_url,
                "-c", "copy",
                "-movflags", "+faststart",
                str(tmp_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

            if proc.returncode != 0:
                err = stderr.decode("utf-8", "replace")[-400:]
                _LOGGER.warning("ffmpeg failed (rc=%s): %s", proc.returncode, err)
                return

            if not tmp_path.exists() or tmp_path.stat().st_size == 0:
                _LOGGER.warning("ffmpeg produced empty MP4")
                return

            # Check Telegram 50MB limit
            size_mb = tmp_path.stat().st_size / (1024 * 1024)
            if size_mb > 50:
                _LOGGER.warning("Video %.1fMB >50MB limit, skipping sendVideo", size_mb)
                return

            # 2) Upload MP4 to Telegram
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendVideo"
            from aiohttp import FormData
            form = FormData()
            form.add_field("chat_id", self.telegram_chat_id)
            from pathlib import Path
            with open(tmp_path, "rb") as f:
                form.add_field(
                    "video",
                    f,
                    filename="vicohome_motion.mp4",
                    content_type="video/mp4",
                )
                form.add_field("caption", caption)
                form.add_field("supports_streaming", "true")

                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=form, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                        result = await resp.json()
                        if not result.get("ok"):
                            _LOGGER.warning("Telegram video error: %s", result.get("description"))

        except asyncio.TimeoutError:
            _LOGGER.error("ffmpeg or Telegram upload timed out")
        except Exception as err:
            _LOGGER.error("Telegram video failed: %s", err)

        finally:
            # 3) Clean up temp file
            if tmp_path.exists():
                tmp_path.unlink()

    async def _async_send_telegram_document(self, doc_bytes: bytes, ext: str, caption: str) -> None:
        """Fallback: send as document upload."""
        try:
            import io
            from aiohttp import FormData
            form = FormData()
            form.add_field("chat_id", self.telegram_chat_id)
            form.add_field(
                "document",
                io.BytesIO(doc_bytes),
                filename=f"vicohome_motion{ext}",
            )
            form.add_field("caption", caption)
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendDocument"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=form, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    result = await resp.json()
                    if not result.get("ok"):
                        _LOGGER.warning("Telegram sendDocument fallback error: %s", result.get("description"))
        except Exception as err:
            _LOGGER.error("Telegram document fallback failed: %s", err)

    # --- Runtime setters (persist in config entry options) ---

    async def async_set_notifications(self, enabled: bool) -> None:
        """Enable/disable notifications."""
        self.notifications_enabled = enabled
        opts = {**(self.entry.options or {}), CONF_NOTIFICATIONS: enabled}
        self.hass.config_entries.async_update_entry(self.entry, options=opts)
        await self.async_request_refresh()

    async def async_set_interval(self, seconds: int) -> None:
        """Set polling interval."""
        self.interval = seconds
        self.update_interval = timedelta(seconds=seconds)
        opts = {**(self.entry.options or {}), CONF_POLLING_INTERVAL: seconds}
        self.hass.config_entries.async_update_entry(self.entry, options=opts)
        await self.async_request_refresh()

    async def async_set_telegram_bot(self, token: str) -> None:
        """Set Telegram bot token."""
        self.telegram_bot_token = token
        opts = {**(self.entry.options or {}), CONF_TELEGRAM_BOT: token}
        self.hass.config_entries.async_update_entry(self.entry, options=opts)
        await self.async_request_refresh()

    async def async_set_telegram_chat(self, chat_id: str) -> None:
        """Set Telegram chat ID."""
        self.telegram_chat_id = chat_id
        opts = {**(self.entry.options or {}), CONF_TELEGRAM_CHAT: chat_id}
        self.hass.config_entries.async_update_entry(self.entry, options=opts)
        await self.async_request_refresh()
