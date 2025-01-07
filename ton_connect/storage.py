import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Generic, TypeVar, cast

from pydantic import BaseModel, ConfigDict, Field
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.mongo_client import AsyncMongoClient

from ton_connect.bridge import Connection

Model = TypeVar("Model", bound="BridgeData")


class BridgeKey(str, Enum):
    CONNECTION = "connection"
    LAST_EVENT_ID = "last_event_id"
    HEARTBEAT = "heartbeat"


class BridgeData(BaseModel):
    model_config = ConfigDict(extra="allow")

    connection: Connection | None = Field(None, description="Connection to wallet object.")
    last_event_id: int | None = Field(None, description="Last wallet event ID.")


class BridgeStorage(ABC, Generic[Model]):
    def __init__(self, entity_id: str) -> None:
        self.entity_id = entity_id
        self.lock = asyncio.Lock()

    @abstractmethod
    async def insert(self, app_name: str, data: Model) -> None: ...

    @abstractmethod
    async def set(self, app_name: str, key: BridgeKey, value: Connection | int) -> None: ...

    @abstractmethod
    async def get(self, app_name: str, key: BridgeKey) -> Connection | int: ...

    @abstractmethod
    async def remove(self, app_name: str, key: BridgeKey) -> None: ...

    @abstractmethod
    async def delete(self, app_name: str) -> None: ...

    async def get_connection(self, app_name: str) -> Connection | None:
        """Get connection from storage."""

        async with self.lock:
            try:
                return cast(Connection, await self.get(app_name, BridgeKey.CONNECTION))
            except KeyError:
                return None

    async def set_connection(self, app_name: str, connection: Connection) -> None:
        """Set connection to storage."""

        async with self.lock:
            await self.set(app_name, BridgeKey.CONNECTION, connection)

    async def get_last_event_id(self, app_name: str) -> int | None:
        async with self.lock:
            return cast(int | None, await self.get(app_name, BridgeKey.LAST_EVENT_ID))

    async def set_last_event_id(self, app_name: str, value: int) -> None:
        async with self.lock:
            await self.set(app_name, BridgeKey.LAST_EVENT_ID, value)


class DictBridgeStorage(BridgeStorage, Generic[Model]):
    STORAGE: dict[str, Model] = {}

    @staticmethod
    def gen_key(app_name: str, key: str) -> str:
        return f"{app_name}:{key}"

    async def delete(self, app_name: str) -> None:
        """Delete storage."""

        key = self.gen_key(app_name, self.entity_id)
        if key in self.STORAGE:
            del self.STORAGE[key]

    async def insert(self, app_name: str, data: Model) -> None:
        """Insert user wallet app to storage."""

        key = self.gen_key(app_name, self.entity_id)
        if key in self.STORAGE:
            raise KeyError("App already exists in storage.")

        self.STORAGE[key] = data

    async def set(self, app_name: str, key: BridgeKey, value: Connection | int) -> None:
        setattr(self.STORAGE[self.gen_key(app_name, self.entity_id)], key.value, value)

    async def get(
        self,
        app_name: str,
        key: BridgeKey,
    ) -> Connection | int:
        return getattr(self.STORAGE[self.gen_key(app_name, self.entity_id)], key)

    async def remove(self, app_name: str, key: BridgeKey) -> None:
        delattr(self.STORAGE[self.gen_key(app_name, self.entity_id)], key.value)


class MongoBridgeStorage(BridgeStorage, Generic[Model]):
    def __init__(
        self,
        entity_id: str,
        client: AsyncMongoClient[dict[str, Any]],
        database: str,
        collection: str,
        primary_key: str = "_id",
    ) -> None:
        super().__init__(entity_id)

        self.client = client
        self.database_name = database
        self.collection_name = collection
        self.primary_key = primary_key

    def gen_search_query(self, app_name: str) -> dict[str, Any]:
        """Generate search query for storage."""

        return {
            self.primary_key: self.entity_id,
            "app_name": app_name,
        }

    @property
    def collection(self) -> AsyncCollection[dict[str, Any]]:
        return self.client[self.database_name][self.collection_name]

    async def ensure_index(self) -> None:
        """Ensure index for storage."""

        await self.collection.create_index([(self.primary_key, 1), ("app_name", 1)], unique=True)
        await self.collection.create_index("heartbeat")

    async def delete(self, app_name: str) -> None:
        """Delete app storage."""

        await self.collection.delete_one(self.gen_search_query(app_name))

    async def insert(self, app_name: str, data: Model) -> None:
        """Insert user wallet app to storage."""

        await self.collection.insert_one(
            {
                self.primary_key: self.entity_id,
                "app_name": app_name,
                "wallet": data.model_dump(
                    mode="json",
                    by_alias=True,
                    exclude_none=True,
                ),
            }
        )

    async def get(
        self,
        app_name: str,
        key: BridgeKey,
    ) -> Connection | int:
        """Get value from storage. Requires extra motor dependency."""

        projection = {key.value: 1, self.primary_key: 1}

        doc = await self.collection.find_one(self.gen_search_query(app_name), projection)
        if not doc:
            raise KeyError("App not found in storage.")

        return getattr(BridgeData.model_validate(doc), key.value)

    async def set(self, app_name: str, key: BridgeKey, value: Connection | int) -> None:
        """Set value to storage. Requires extra motor dependency."""

        await self.collection.update_one(
            self.gen_search_query(app_name),
            {
                "$set": {
                    key.value: value
                    if isinstance(value, int)
                    else value.model_dump(mode="json", by_alias=True, exclude_none=True)
                }
            },
        )

    async def remove(self, app_name: str, key: BridgeKey) -> None:
        """Remove value from storage. Requires extra motor dependency."""

        await self.collection.update_one(
            self.gen_search_query(app_name),
            {"$unset": {key.value: ""}},
        )
