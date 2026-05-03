"""Constants for VicoHome integration."""

DOMAIN = "vicohome"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_REGION = "region"
CONF_POLLING_INTERVAL = "polling_interval"

CONF_NOTIFICATIONS = "notifications_enabled"
CONF_TELEGRAM_BOT = "telegram_bot_token"
CONF_TELEGRAM_CHAT = "telegram_chat_id"

DEFAULT_REGION = "eu"
DEFAULT_POLLING_INTERVAL = 180  # seconds (3 minutes)

PLATFORMS = ["sensor", "binary_sensor", "camera", "switch", "number", "text"]
