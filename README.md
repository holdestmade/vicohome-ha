![VicoHome Banner](custom_components/vicohome/brand/banner.png)

## VicoHome for Home Assistant

Custom integration for **VicoHome CG1** cloud cameras in Home Assistant.

> ⚠️ **Unofficial & community-driven.** This integration uses the undocumented VicoHome cloud API. VicoHome may change or restrict access at any time. Use at your own risk.

### Features

- 📹 **Motion Detection** via cloud events (no local stream)
- 📸 **Snapshot Camera** entity showing the last motion event image
- 📊 **Event Sensor** counting events in the last hour
- 🔔 **Telegram Notifications** with photo + video (configurable)
- ⚙️ **Runtime settings** via HA UI: notification toggle, polling interval, Telegram bot/token

### Requirements

- Home Assistant 2024.0.0 or newer
- VicoHome account (e-mail + password)
- ffmpeg (pre-installed in HA OS / Docker; for bare-metal: `apt install ffmpeg`)

### Installation

#### HACS (recommended)
1. Add the repository as a custom repository in HACS:
   - Go to **HACS → Integrations**
   - Click **⋮ → Custom repositories**
   - URL: `https://github.com/TomTje/vicohome-ha`
   - Category: **Integration**
2. Search for **VicoHome** and install.
3. Restart Home Assistant.

#### Manual
1. Download the `custom_components/vicohome` folder.
2. Copy it into `config/custom_components/vicohome`.
3. Restart Home Assistant.

#### Configuration
1. Go to **Settings → Devices & Services → Add Integration**.
2. Select **VicoHome** (or search for it).
3. Enter:
   - **E-Mail**
   - **Password**
   - **Region** (EU or US)
   - **Polling Interval** (default: 180 s)
4. After setup, use the new entities to configure Telegram:
   - `switch.vicohome_benachrichtigungen` — ON/OFF
   - `text.vicohome_telegram_bot_token` — your Telegram bot token
   - `text.vicohome_telegram_empfanger_id` — your Telegram chat ID
   - `number.vicohome_aktualisierungsintervall` — seconds (60–3600)

### Supported Devices

| Model | Status |
|---|---|
| CG1 | ✅ Tested & confirmed |
| Other VicoHome models | ❓ Not tested yet — open an issue if you try one. |

### Entities

| Entity | Type | Description |
|---|---|---|
| `sensor.vicohome_events_1h` | Sensor | Number of events in the last hour |
| `sensor.vicohome_last_event` | Sensor | Details of the latest event (timestamp, traceId, imageUrl, videoUrl) |
| `binary_sensor.vicohome_bewegung` | Binary | Motion detected (triggers on new event) |
| `camera.vicohome_camera` | Camera | Snapshot from the last event |
| `switch.vicohome_benachrichtigungen` | Switch | Telegram notifications ON/OFF |
| `number.vicohome_aktualisierungsintervall` | Number | Polling interval (s) |
| `text.vicohome_telegram_bot_token` | Text | Bot token (password mode) |
| `text.vicohome_telegram_empfanger_id` | Text | Chat/recipient ID |

### How It Works

1. The coordinator periodically logs in to `api-{region}.vicohome.io` and fetches recent events.
2. If a **new event** (new `traceId`) is found, the binary sensor flips to `on`.
3. If notifications are enabled, it sends a Telegram message with:
   - Formatted text (device name, time, trace ID)
   - Inline photo (snapshot)
   - MP4 video (transcoded from M3U8 via ffmpeg, max 50 MB)
4. All temporary files in `/tmp/` are cleaned up immediately after upload.

### Roadmap / Ideas

- [ ] Native Home Assistant camera stream support (live view)
- [ ] HA service to manually trigger event refresh
- [ ] Cloud-recorded playback from dashboard
- [ ] Support for additional VicoHome camera models

### Troubleshooting

| Issue | Fix |
|---|---|
| "cannot connect" during setup | Check e-mail/password and region (EU vs US). |
| Camera shows *Unavailable* | No motion events in the last hour — trigger motion or wait. |
| No Telegram video received | Video might exceed 50 MB or URL expired. Lower resolution in VicoHome app or reduce polling interval. |
| ffmpeg timeout | Ensure `/tmp` has enough space. For large M3U8 playlists, video may exceed 120 s transcoding. |

### Contributing

Tested on a new VicoHome model? Open an issue with model name + your region so we can expand the compatibility list.

### License

MIT © 2026 TomTje
