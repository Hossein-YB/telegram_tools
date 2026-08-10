import asyncio
import time

from pyrogram.errors import SessionPasswordNeeded
from pyrogram.types import SentCode

from forwarder_client.base import ForwardBot
from config import API_ID, API_HASH
from utils.manage_files import generate_session_path
import logging

log = logging.getLogger(__name__)


class AccountManager:
    def __init__(self):
        self.clients = {}
        self.last_usage_client = {}
        self.pending_auth = {}

    async def create_instance_forwarder(self, phone_number: str):
        session_path = generate_session_path(phone_number)
        client = ForwardBot(name=session_path, api_id=API_ID, api_hash=API_HASH, phone_number=phone_number)
        try:
            is_authorized = await client.connect()
            if is_authorized:
                self.clients[phone_number] = client
                self.last_usage_client[client] = time.time()
                return True
            else:
                self.pending_auth[phone_number] = client
                return False
        except Exception as e:
            try:
                await client.disconnect()
            except:
                pass
            raise

    async def send_code(self, phone_number: str) -> SentCode:
        if phone_number not in self.pending_auth:
            raise ValueError(f"Phone number {phone_number} not in pending authorization")

        client = self.pending_auth[phone_number]

        try:
            sent_code = await client.send_code(phone_number)
            return sent_code
        except Exception as e:
            log.error(f"❌ Error sending code to {phone_number}: {e}")
            try:
                await client.disconnect()
                del self.pending_auth[phone_number]
            except:
                pass
            raise

    async def verify_code(self, phone_number: str, code: str, phone_code_hash: SentCode, password: str = None):

        if phone_number not in self.pending_auth:
            raise ValueError(f"Phone number {phone_number} not in pending authorization")

        client = self.pending_auth[phone_number]

        try:
            await client.sign_in(phone_number=phone_number, phone_code_hash=phone_code_hash, code=code)
        except SessionPasswordNeeded as e:
            await client.check_password(password)
        finally:
            if await client.connect():
                self.clients[phone_number] = client
                del self.pending_auth[phone_number]
                self.last_usage_client[client] = time.time()
                return client

    async def new_client(self, phone_number):
        await self.create_instance_forwarder(phone_number)
        return await self.send_code(phone_number)

