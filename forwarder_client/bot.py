import asyncio
from typing import Optional, List
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import Message
from pyrogram.handlers import MessageHandler
import logging
from db.models import ForwardMessage, GroupInfo, ForwardHistory
from forwarder_client.messages import MessagesText
from config import SUDO_ID, FORWARD_INTERVAL_MINUTES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForwardBot(Client):
    def __init__(self, name, api_id, api_hash):
        self.is_forwarding: bool = False
        self.f_message: Optional[Message] = None
        self.db_message: Optional[ForwardMessage] = None
        self.texts = MessagesText()

        self.group_ids_not_forward: List[int] = []
        self.group_ids: List[int] = []

        super().__init__(name=name, api_id=api_id, api_hash=api_hash)

    def is_sudo(self, msg: Message):

        return msg.from_user.id in SUDO_IDS

    async def check_status(self, clt, msg: Message):
        if not self.is_sudo(msg):
            return False

        await msg.reply_text(self.texts.status_text())

    async def stop_forwarding(self, clt, msg: Message):
        if not self.is_sudo(msg):
            return False

        self.is_forwarding = False
        return await msg.reply_text(self.texts.STOP_FORWARDING)

    async def set_new_message(self, clt, msg: Message):
        if not self.is_sudo(msg):
            return False

        if not msg.reply_to_message:
            await msg.reply_text(self.texts.ERROR_NO_REPLY)
            return

        try:
            self.f_message = msg.reply_to_message.forward_origin

            source_chat_id = self.f_message.chat.id
            source_message_id = self.f_message.message_id
            self.db_message = ForwardMessage.add_message(source_chat_id, source_message_id)
            await self.forward_messages(chat_id=msg.from_user.id,
                                        from_chat_id=source_chat_id,
                                        message_ids=source_message_id)
            await msg.reply_text(self.texts.SET_NEW_MESSAGE_SUCCESS)
        except Exception as e:
            print(e)

    async def get_groups(self):
        count = 0
        self.group_ids.clear()

        async for chat in self.get_dialogs():
            if chat.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
                continue

            group_link = (
                f"https://t.me/{chat.chat.username}"
                if chat.chat.username
                else None
            )

            GroupInfo.add_group(
                group_id=chat.chat.id,
                group_title=chat.chat.title,
                group_username=chat.chat.username,
                group_link=group_link,
            )

            self.group_ids.append(chat.chat.id)
            count += 1

        return count

    async def forward_to_all_group(self, clt, msg: Message):
        if not self.is_sudo(msg):
            return False

        if not self.f_message:
            return await msg.reply_text(self.texts.MESSAGE_NOT_FOUND)

        if self.is_forwarding:
            return await msg.reply_text(self.texts.ALREADY_FORWARDING)

        count = await self.get_groups()
        if not self.group_ids:
            return await msg.reply_text(self.texts.GROUPS_NOT_FOUND)

        await msg.reply_text(self.texts.start_forward_group_count(count))
        self.is_forwarding = True

        while self.is_forwarding:
            count = await self.forward_message_in_group()
            await msg.reply_text(self.texts.next_round_forward(count))
            await asyncio.sleep(FORWARD_INTERVAL_MINUTES)

        return None

    async def forward_message_in_group(self):
        self.is_forwarding = True

        if not self.f_message:
            self.is_forwarding = False
            return
        count = 0
        try:
            for group_id in self.group_ids:
                if not self.is_forwarding:
                    break
                try:

                    await self.forward_messages(chat_id=group_id,
                                                from_chat_id=self.db_message.source_chat_id,
                                                message_ids=self.db_message.source_message_id)

                    ForwardHistory.create_history(message_id=self.db_message.id,
                                                  group_id=group_id, success=True, error="")

                    ForwardHistory.create_history(
                        message_id=self.db_message.id,
                        group_id=group_id,
                        success=True
                    )
                    count += 1
                except Exception as e:
                    self.group_ids_not_forward.append(group_id)
                    GroupInfo.set_ban(group_id)
                    ForwardHistory.create_history(
                        message_id=self.db_message.id,
                        group_id=group_id,
                        success=False,
                        error=str(e)
                    )
                    logger.exception(e)

        except Exception as e:
            logger.exception(e)

        finally:
            return count

    async def start(self):
        self.add_handler(MessageHandler(self.set_new_message, filters.command("set", prefixes="!")))
        self.add_handler(MessageHandler(self.forward_to_all_group, filters.command("start", prefixes="!")))
        self.add_handler(MessageHandler(self.stop_forwarding, filters.command("stop", prefixes="!")))
        self.add_handler(MessageHandler(self.check_status, filters.command("check", prefixes="!")))

        return await super().start()
