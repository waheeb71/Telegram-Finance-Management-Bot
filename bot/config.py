import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOT_TOKEN: str = "7891234567:AAExampleTokenForYemenCyberFinanceBot"
    SUPER_ADMIN_ID: int = 123456789
    
    NOTIFICATION_GROUP_ID: str = "0"
    NOTIFICATION_GROUP_IDS: str = ""
    STORAGE_CHANNEL_ID: int = 0
    
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:npg_mKwgkb6FWD9B@ep-noisy-glitter-aynq0lr1-pooler.c-5.us-east-2.aws.neon.tech/neondb?ssl=require"
    REDIS_URL: Optional[str] = None
    WEBHOOK_URL: Optional[str] = None
    
    BOT_LANGUAGE: str = "ar"
    CURRENCY_SYMBOL: str = "ريال"
    TIMEZONE: str = "Asia/Aden"

    def get_notification_group_ids(self) -> list[int]:
        raw_val = self.NOTIFICATION_GROUP_IDS.strip() or str(self.NOTIFICATION_GROUP_ID).strip()
        if not raw_val or raw_val == "0":
            return []
        
        group_ids = []
        for part in raw_val.split(","):
            part = part.strip()
            if part and part != "0":
                try:
                    group_ids.append(int(part))
                except ValueError:
                    pass
        return group_ids

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

