from pathlib import Path

from dotenv import find_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SRC_DIR = Path(__file__).parent
IMAGES = SRC_DIR / "images"


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=find_dotenv(),
                                      env_file_encoding="utf-8",
                                      extra="ignore",
                                      validate_by_alias=True)

    token: str = Field(validation_alias="TOKEN")
    log_chat_id: int = Field(validation_alias="LOG_CHAT_ID")
    admin_id: int = Field(validation_alias="ADMIN_ID")

    target_chat: str = Field(validation_alias="TARGET_CHAT")
    dice_delay: float = Field(default=4.1, validation_alias="DICE_DELAY")
    card_delay: float = Field(default=2, validation_alias="CARD_DELAY")


config = Config()
