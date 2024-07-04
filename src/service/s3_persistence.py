import os
import pickle
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union, cast, overload

import boto3
from telegram._utils.types import FilePathInput
from telegram.ext import BasePersistence, PersistenceInput
from telegram.ext._contexttypes import ContextTypes
from telegram.ext._utils.types import BD, CD, UD, CDCData, ConversationDict, ConversationKey


class S3Persistence(BasePersistence[UD, CD, BD]):
    __slots__ = (
        "bot_data",
        "callback_data",
        "chat_data",
        "context_types",
        "conversations",
        "filepath",
        "on_flush",
        "single_file",
        "user_data",
        "s3"
    )

    @overload
    def __init__(
            self: "S3Persistence[Dict[Any, Any], Dict[Any, Any], Dict[Any, Any]]",
            filepath: FilePathInput,
            store_data: Optional[PersistenceInput] = None,
            single_file: bool = True,
            on_flush: bool = False,
            update_interval: float = 60,
    ):
        ...

    @overload
    def __init__(
            self: "S3Persistence[UD, CD, BD]",
            filepath: FilePathInput,
            store_data: Optional[PersistenceInput] = None,
            single_file: bool = True,
            on_flush: bool = False,
            update_interval: float = 60,
            context_types: Optional[ContextTypes[Any, UD, CD, BD]] = None,
    ):
        ...

    def __init__(
            self,
            filepath: FilePathInput,
            store_data: Optional[PersistenceInput] = None,
            single_file: bool = True,
            on_flush: bool = False,
            update_interval: float = 60,
            context_types: Optional[ContextTypes[Any, UD, CD, BD]] = None,
    ):
        super().__init__(store_data=store_data, update_interval=update_interval)
        self.filepath: Path = Path(filepath)
        self.single_file: Optional[bool] = single_file
        self.on_flush: Optional[bool] = on_flush
        self.user_data: Optional[Dict[int, UD]] = None
        self.chat_data: Optional[Dict[int, CD]] = None
        self.bot_data: Optional[BD] = None
        self.callback_data: Optional[CDCData] = None
        self.conversations: Optional[Dict[str, Dict[Tuple[Union[int, str], ...], object]]] = None
        self.context_types: ContextTypes[Any, UD, CD, BD] = cast(
            ContextTypes[Any, UD, CD, BD], context_types or ContextTypes()
        )
        """
        Initializes the S3 object.
        """
        session = boto3.session.Session()
        self.s3 = session.client(
            service_name='s3',
            endpoint_url='https://storage.yandexcloud.net'
        )

    def _load_singlefile(self) -> None:
        try:
            try:
                get_object_response = self.s3.get_object(Bucket=os.getenv('S3_BUCKET'), Key=self.filepath.as_posix())
                data = pickle.loads(get_object_response['Body'].read())
            except Exception as exc:
                data = {}

            self.user_data = data["user_data"]
            self.chat_data = data["chat_data"]
            # For backwards compatibility with files not containing bot data
            self.bot_data = data.get("bot_data", self.context_types.bot_data())
            self.callback_data = data.get("callback_data", {})
            self.conversations = data["conversations"]
        except KeyError:
            self.conversations = {}
            self.user_data = {}
            self.chat_data = {}
            self.bot_data = self.context_types.bot_data()
            self.callback_data = None
        except pickle.UnpicklingError as exc:
            filename = self.filepath.name
            raise TypeError(f"File {filename} does not contain valid pickle data") from exc
        except Exception as exc:
            raise TypeError(f"Something went wrong unpickling {self.filepath.name}") from exc

    def _load_file(self, filepath: Path) -> Any:
        try:
            get_object_response = self.s3.get_object(Bucket=os.getenv('S3_BUCKET'), Key=filepath.as_posix())
            return pickle.loads(get_object_response['Body'].read())
        except OSError:
            return None
        except pickle.UnpicklingError as exc:
            raise TypeError(f"File {filepath.name} does not contain valid pickle data") from exc
        except Exception as exc:
            raise TypeError(f"Something went wrong unpickling {filepath.name}") from exc

    def _dump_singlefile(self) -> None:
        data = {
            "conversations": self.conversations,
            "user_data": self.user_data,
            "chat_data": self.chat_data,
            "bot_data": self.bot_data,
            "callback_data": self.callback_data,
        }
        pickle_byte_obj = pickle.dumps(data)
        self.s3.put_object(Bucket=os.getenv('S3_BUCKET'), Key=self.filepath.as_posix(),
                           Body=pickle_byte_obj, StorageClass='COLD')

    def _dump_file(self, filepath: Path, data: object) -> None:
        pickle_byte_obj = pickle.dumps(data)
        self.s3.put_object(Bucket=os.getenv('S3_BUCKET'), Key=filepath.as_posix(),
                           Body=pickle_byte_obj, StorageClass='COLD')

    async def get_user_data(self) -> Dict[int, UD]:
        """Returns the user_data from the pickle file if it exists or an empty :obj:`dict`."""
        if self.user_data:
            pass
        elif not self.single_file:
            data = self._load_file(Path(f"{self.filepath}_user_data"))
            if not data:
                data = {}
            self.user_data = data
        else:
            self._load_singlefile()
        return deepcopy(self.user_data)  # type: ignore[arg-type]

    async def get_chat_data(self) -> Dict[int, CD]:
        """Returns the chat_data from the pickle file if it exists or an empty :obj:`dict`."""
        if self.chat_data:
            pass
        elif not self.single_file:
            data = self._load_file(Path(f"{self.filepath}_chat_data"))
            if not data:
                data = {}
            self.chat_data = data
        else:
            self._load_singlefile()
        return deepcopy(self.chat_data)  # type: ignore[arg-type]

    async def get_bot_data(self) -> BD:
        """Returns the bot_data from the pickle file if it exists or an empty object of type"""
        if self.bot_data:
            pass
        elif not self.single_file:
            data = self._load_file(Path(f"{self.filepath}_bot_data"))
            if not data:
                data = self.context_types.bot_data()
            self.bot_data = data
        else:
            self._load_singlefile()
        return deepcopy(self.bot_data)  # type: ignore[return-value]

    async def get_callback_data(self) -> Optional[CDCData]:
        """Returns the callback data from the pickle file if it exists or :obj:`None`."""
        if self.callback_data:
            pass
        elif not self.single_file:
            data = self._load_file(Path(f"{self.filepath}_callback_data"))
            if not data:
                data = None
            self.callback_data = data
        else:
            self._load_singlefile()
        if self.callback_data is None:
            return None
        return deepcopy(self.callback_data)

    async def get_conversations(self, name: str) -> ConversationDict:
        """Returns the conversations from the pickle file if it exists or an empty dict."""
        if self.conversations:
            pass
        elif not self.single_file:
            data = self._load_file(Path(f"{self.filepath}_conversations"))
            if not data:
                data = {name: {}}
            self.conversations = data
        else:
            self._load_singlefile()
        return self.conversations.get(name, {}).copy()  # type: ignore[union-attr]

    async def update_conversation(
            self, name: str, key: ConversationKey, new_state: Optional[object]
    ) -> None:
        """Will update the conversations for the given handler and depending on :attr:`on_flush`
        save the pickle file."""
        if not self.conversations:
            self.conversations = {}
        if self.conversations.setdefault(name, {}).get(key) == new_state:
            return
        self.conversations[name][key] = new_state
        if not self.on_flush:
            if not self.single_file:
                self._dump_file(Path(f"{self.filepath}_conversations"), self.conversations)
            else:
                self._dump_singlefile()

    async def update_user_data(self, user_id: int, data: UD) -> None:
        """Will update the user_data and depending on :attr:`on_flush` save the pickle file."""
        if self.user_data is None:
            self.user_data = {}
        if self.user_data.get(user_id) == data:
            return
        self.user_data[user_id] = data
        if not self.on_flush:
            if not self.single_file:
                self._dump_file(Path(f"{self.filepath}_user_data"), self.user_data)
            else:
                self._dump_singlefile()

    async def update_chat_data(self, chat_id: int, data: CD) -> None:
        """Will update the chat_data and depending on :attr:`on_flush` save the pickle file."""
        if self.chat_data is None:
            self.chat_data = {}
        if self.chat_data.get(chat_id) == data:
            return
        self.chat_data[chat_id] = data
        if not self.on_flush:
            if not self.single_file:
                self._dump_file(Path(f"{self.filepath}_chat_data"), self.chat_data)
            else:
                self._dump_singlefile()

    async def update_bot_data(self, data: BD) -> None:
        """Will update the bot_data and depending on :attr:`on_flush` save the pickle file. """
        if self.bot_data == data:
            return
        self.bot_data = data
        if not self.on_flush:
            if not self.single_file:
                self._dump_file(Path(f"{self.filepath}_bot_data"), self.bot_data)
            else:
                self._dump_singlefile()

    async def update_callback_data(self, data: CDCData) -> None:
        """Will update the callback_data (if changed) and depending on 
        :attr:`on_flush` save the
        pickle file."""
        if self.callback_data == data:
            return
        self.callback_data = data
        if not self.on_flush:
            if not self.single_file:
                self._dump_file(Path(f"{self.filepath}_callback_data"), self.callback_data)
            else:
                self._dump_singlefile()

    async def drop_chat_data(self, chat_id: int) -> None:
        """Will delete the specified key from the ``chat_data`` and depending on
        :attr:`on_flush` save the pickle file."""
        if self.chat_data is None:
            return
        self.chat_data.pop(chat_id, None)

        if not self.on_flush:
            if not self.single_file:
                self._dump_file(Path(f"{self.filepath}_chat_data"), self.chat_data)
            else:
                self._dump_singlefile()

    async def drop_user_data(self, user_id: int) -> None:
        """Will delete the specified key from the ``user_data`` and depending on
        :attr:`on_flush` save the pickle file."""
        if self.user_data is None:
            return
        self.user_data.pop(user_id, None)

        if not self.on_flush:
            if not self.single_file:
                self._dump_file(Path(f"{self.filepath}_user_data"), self.user_data)
            else:
                self._dump_singlefile()

    async def refresh_user_data(self, user_id: int, user_data: UD) -> None:
        pass

    async def refresh_chat_data(self, chat_id: int, chat_data: CD) -> None:
        pass

    async def refresh_bot_data(self, bot_data: BD) -> None:
        pass

    async def flush(self) -> None:
        """Will save all data in memory to pickle file(s)."""
        if self.single_file:
            if (
                    self.user_data
                    or self.chat_data
                    or self.bot_data
                    or self.callback_data
                    or self.conversations
            ):
                self._dump_singlefile()
        else:
            if self.user_data:
                self._dump_file(Path(f"{self.filepath}_user_data"), self.user_data)
            if self.chat_data:
                self._dump_file(Path(f"{self.filepath}_chat_data"), self.chat_data)
            if self.bot_data:
                self._dump_file(Path(f"{self.filepath}_bot_data"), self.bot_data)
            if self.callback_data:
                self._dump_file(Path(f"{self.filepath}_callback_data"), self.callback_data)
            if self.conversations:
                self._dump_file(Path(f"{self.filepath}_conversations"), self.conversations)
