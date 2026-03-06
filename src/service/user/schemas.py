from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    full_name: str
    prompt: str
    start_number: int
    dice_numbers: list[int]
    remaining_rolls: int
    has_finished: bool
    is_frozen: bool
    frozen_until: datetime
    created_at: datetime

    @field_validator("dice_numbers", mode="before")
    def parse_dice_numbers(cls, value: str) -> list[int]:
        if not value:
            return []
        return [int(i) for i in value.split(',')]
