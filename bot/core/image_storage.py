from aiogram import Bot
from bot.config import settings
from bot.core.logger import logger

class ImageStorageManager:
    @staticmethod
    async def upload_photo(bot: Bot, photo_file_id: str, caption: str = "") -> dict:
        """
        Uploads/forwards a photo to the dedicated Telegram Storage Channel.
        Returns a dict containing 'file_id' and 'message_id'.
        """
        if not settings.STORAGE_CHANNEL_ID or settings.STORAGE_CHANNEL_ID == 0:
            logger.info("STORAGE_CHANNEL_ID not set. Using raw file_id directly.")
            return {"file_id": photo_file_id, "message_id": None}
        
        try:
            sent_msg = await bot.send_photo(
                chat_id=settings.STORAGE_CHANNEL_ID,
                photo=photo_file_id,
                caption=caption
            )
            return {
                "file_id": sent_msg.photo[-1].file_id,
                "message_id": sent_msg.message_id
            }
        except Exception as e:
            logger.error(f"Failed to forward photo to storage channel: {e}")
            return {"file_id": photo_file_id, "message_id": None}

    @staticmethod
    async def send_stored_photo(bot: Bot, chat_id: int, file_id: str, caption: str = ""):
        """
        Sends a stored photo to a specific Telegram user or group.
        """
        try:
            await bot.send_photo(
                chat_id=chat_id,
                photo=file_id,
                caption=caption
            )
        except Exception as e:
            logger.error(f"Failed to send stored photo: {e}")
            raise e
