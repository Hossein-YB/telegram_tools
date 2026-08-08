import asyncio
from config import API_ID, API_HASH, SUDO_IDS, TOKEN
from client_manager.base import ClientManger
from db.create_table import init_database


async def main():
    print("##### CREATE DATABASE #####")
    init_database(SUDO_IDS)
    print("##### RUN BOT  #####")
    bot = ClientManger(name="ftag", api_hash=API_HASH, api_id=API_ID, bot_token=TOKEN)
    await bot.start()


if __name__ == "__main__":
    # run loop
    loop = asyncio.new_event_loop()
    loop.create_task(main())
    loop.run_forever()
