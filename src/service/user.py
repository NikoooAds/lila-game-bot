from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime

import aiosqlite
from pydantic import BaseModel, Field, ConfigDict, field_validator


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: int
    full_name: str
    phone: str | None = None
    prompts: list[str]
    start_number: int
    dice_numbers: list[int]
    remaining_rolls: int
    has_finished: bool
    is_frozen: bool
    frozen_until: datetime
    created_at: datetime

    @field_validator("prompts", mode="before")
    def parse_prompts(cls, value: str) -> list[str]:
        if not value:
            return []
        return value.split('~')

    @field_validator("dice_numbers", mode="before")
    def parse_dice_numbers(cls, value: str) -> list[int]:
        if not value:
            return []
        return [int(i) for i in value.split(',')]


class UserStorageService:

    def __init__(self, db_path: str = "database.sqlite3"):
        self.db_path = db_path

    @asynccontextmanager
    async def _session_maker(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # await db.execute("PRAGMA foreign_keys = ON")
            yield db

    async def init_db(self):
        async with self._session_maker() as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    phone TEXT DEFAULT NULL,
                    prompts TEXT NOT NULL DEFAULT '',
                    start_number INTEGER DEFAULT 0,
                    dice_numbers TEXT DEFAULT '',
                    remaining_rolls INTEGER DEFAULT 5,
                    is_frozen BOOLEAN DEFAULT false,
                    frozen_until TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    has_finished BOOLEAN DEFAULT false,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()

    async def create_user(self, user_id: int, full_name: str) -> int:
        async with self._session_maker() as db:
            cursor = await db.execute(
                "INSERT INTO users (id, full_name) VALUES (?, ?)",
                (user_id, full_name)
            )
            await db.commit()
            return cursor.lastrowid

    async def get(self, user_id: int) -> User | None:
        async with self._session_maker() as db:
            async with db.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return User(**dict(row)) if row else None

    async def delete(self, user_id: int) -> int:
        async with self._session_maker() as db:
            cursor = await db.execute("DELETE FROM users WHERE id = ?", (user_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def update(self, user_id: int, data: dict):
        if not data:
            return None

        fields = []
        values = []
        for key, value in data.items():
            fields.append(f"{key} = ?")
            values.append(value)
        values.append(user_id)
        async with self._session_maker() as db:
            async with db.execute(
                f"UPDATE users SET {','.join(fields)} WHERE id = ?", tuple(values)
            ) as cursor:
                await db.commit()
                return cursor.rowcount

    async def set_start_number(self, user_id: int, number: int):
        resp = await self.update(user_id, {"start_number": number})
        return bool(resp)

    async def add_prompt(self, user_id: int, text: str):
        if row := await self.get(user_id):
            row.prompts.append(text)
            resp = await self.update(user_id, {"prompts": '~'.join(row.prompts)})
            return bool(resp)
        return None

    async def take_dice(self, user_id: int, number: int):
        if row := await self.get(user_id):
            row.dice_numbers.append(number)
            value = ','.join(map(str, row.dice_numbers))
            resp = await self.update(
                user_id,
                {
                    "dice_numbers": value,
                    "remaining_rolls": row.remaining_rolls - 1,
                }
            )
            return bool(resp)
        return False

    async def lock_user(self, user_id: int, until_date: datetime):
        resp = await self.update(
            user_id,
            {"is_frozen": True, "frozen_until": until_date},
        )
        return bool(resp)

    async def finish_the_game(self, user_id: int):
        resp = await self.update(user_id, {"has_finished": True})
        return bool(resp)

    async def unlock_user(self, user_id: int):
        resp = await self.update(user_id, {"is_frozen": False})
        return bool(resp)

    async def add_more_rolls(self, user_id: int, count: int = 5):
        resp = await self.update(user_id, {"remaining_rolls": count})
        return bool(resp)

    async def get_frozen_users(self) -> list[User]:
        async with self._session_maker() as db:
            async with db.execute(
                "SELECT * FROM users WHERE is_frozen == True"
            ) as cursor:
                rows = await cursor.fetchall()
                return [User(**dict(row)) for row in rows]

    async def get_all(self) -> list[User]:
        async with self._session_maker() as db:
            async with db.execute(
                "SELECT * FROM users ORDER BY created_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [User(**dict(row)) for row in rows]
