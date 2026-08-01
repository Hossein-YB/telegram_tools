import asyncio
from config import API_ID, API_HASH
from forwarder_client.bot import ForwardBot
from db.models import init_database


async def main():
    print("##### CREATE DATABASE #####")
    init_database()
    print("##### RUN BOT  #####")
    bot = ForwardBot(name="ftag", api_hash=API_HASH, api_id=API_ID)
    await bot.start()


if __name__ == "__main__":
    # run loop
    loop = asyncio.new_event_loop()
    loop.create_task(main())
    loop.run_forever()
