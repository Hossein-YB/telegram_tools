import asyncio
from typing import Optional, List
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.types import Message, Chat
from pyrogram.handlers import MessageHandler
import logging
from db.models import ForwardMessage, GroupInfo, ForwardHistory
from forwarder_client.messages import MessagesText
from config import SUDO_IDS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForwardBot(Client):
    def __init__(self, name, api_id, api_hash):
        self.is_forwarding: bool = False
        self.db_message: Optional[ForwardMessage] = None
        self.texts = MessagesText()

        self.group_ids_not_forward: List[int] = []
        self.group_ids: List[int] = []
        self.groups: List[Chat] = []
        self.wait_time_between_forward: int = 900
        super().__init__(name=name, api_id=api_id, api_hash=api_hash)

    def is_sudo(self, msg: Message):
        return msg.from_user.id in SUDO_IDS

    async def check_status(self, clt, msg: Message):
        if not self.is_sudo(msg):
            return False

        await msg.reply_text(self.texts.status_text())

    async def help_message(self, clt, msg: Message):
        if not self.is_sudo(msg):
            return False

        await msg.reply_text(self.texts.HELP)

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
            f_message = msg.reply_to_message.forward_origin

            source_chat_id = f_message.chat.id
            source_message_id = f_message.message_id
            self.db_message = ForwardMessage.add_message(source_chat_id, source_message_id)
            await self.forward_messages(chat_id=msg.from_user.id,
                                        from_chat_id=source_chat_id,
                                        message_ids=source_message_id)
            await msg.reply_text(self.texts.SET_NEW_MESSAGE_SUCCESS)
        except Exception as e:
            print(e)

    async def get_groups(self, clt, msg: Message, send_message: bool=True):
        self.group_ids.clear()
        self.groups.clear()

        async for chat in self.get_dialogs():
            if chat.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
                continue

            GroupInfo.add_group(
                group_id=chat.chat.id,
                group_title=chat.chat.title,
                group_username=chat.chat.username
            )

            self.group_ids.append(chat.chat.id)
            self.groups.append(chat.chat)

        if msg and send_message:
            await msg.reply_text(self.texts.get_group_list(self.groups))

        return True

    async def forward_to_all_group(self, clt, msg: Message):
        if not self.is_sudo(msg):
            return False

        if not self.db_message:
            return await msg.reply_text(self.texts.MESSAGE_NOT_FOUND)

        if self.is_forwarding:
            return await msg.reply_text(self.texts.ALREADY_FORWARDING)

        count = await self.get_groups(clt, msg)
        if not self.group_ids:
            return await msg.reply_text(self.texts.GROUPS_NOT_FOUND)

        await msg.reply_text(self.texts.start_forward_group_count(count))
        self.is_forwarding = True

        num = msg.text.split(" ")[-1]
        if num and num.isdigit():
            num = int(num)
        else:
            num = 1

        for i in range(num):
            count = await self.forward_message_in_group()
            await msg.reply_text(self.texts.next_round_forward(count, self.wait_time_between_forward/60))
            await asyncio.sleep(self.wait_time_between_forward)

        return None

    async def forward_message_in_group(self):
        self.is_forwarding = True

        if not self.db_message:
            self.is_forwarding = False
            return
        count = 0
        try:
            for group_id in self.group_ids:
                if not self.is_forwarding:
                    break
                try:
                    await self.read_chat_history(group_id)
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

    async def forward_to_all_group_once(self, clt, msg: Message):
        if not self.is_sudo(msg):
            return False

        if not msg.reply_to_message:
            await msg.reply_text(self.texts.ERROR_NO_REPLY)
            return

        try:
            f_message = msg.reply_to_message.forward_origin

            source_chat_id = f_message.chat.id
            source_message_id = f_message.message_id
            await self.get_groups(clt, msg)
            if not self.group_ids:
                return await msg.reply_text(self.texts.GROUPS_NOT_FOUND)
            count = 0
            for group_id in self.group_ids:
                try:
                    await self.read_chat_history(group_id)
                    await self.forward_messages(chat_id=group_id,
                                                from_chat_id=source_chat_id,
                                                message_ids=source_message_id)
                    count += 1
                except Exception as e:
                    await msg.reply_text(self.texts.error_to_forward_in_group(group_id, e))
            else:
                await msg.reply_text(self.texts.forward_success_count(count))
        except Exception as e:
            print(e)

    async def set_wait_time(self, clt, msg: Message):

        num = msg.text.split(" ")[-1]
        if num and num.isdigit():
            self.wait_time_between_forward = int(num) * 60

        return await msg.reply_text(self.texts.set_wait_time_between_forward(self.wait_time_between_forward))

    async def join_group(self, clt, msg: Message):
        text = msg.text

        text = text.replace("!join", "").strip()
        try:
            chat = await self.join_chat(text)
            await msg.reply_text(self.texts.join_chat_success(chat.title, chat.id))
            GroupInfo.add_group(
                group_id=chat.id,
                group_title=chat.title,
                group_username=chat.username,
                group_link=text
            )
        except Exception as e:
            print(e)

    async def start(self):
        # helpers
        self.add_handler(MessageHandler(self.check_status, filters.command("check", prefixes="!")))
        self.add_handler(MessageHandler(self.help_message, filters.command("help", prefixes="!")))

        # forward commands
        self.add_handler(MessageHandler(self.set_new_message, filters.command("set", prefixes="!")))
        self.add_handler(MessageHandler(self.forward_to_all_group, filters.regex("^!strat ?(\d+)?$")))
        self.add_handler(MessageHandler(self.stop_forwarding, filters.command("stop", prefixes="!")))
        self.add_handler(MessageHandler(self.forward_to_all_group_once, filters.command("fta", prefixes="!")))
        self.add_handler(MessageHandler(self.set_wait_time, filters.regex("^!time ?(\d+)?$")))

        # groups manage command
        self.add_handler(MessageHandler(self.get_groups, filters.command("group", prefixes="!")))

        # join_to_group
        self.add_handler(MessageHandler(self.join_group, filters.regex("^!join")))

        return await super().start()
