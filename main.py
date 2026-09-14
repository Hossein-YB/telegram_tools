import asyncio
from pyrogram import idle
from config import API_ID, API_HASH, SUDO_IDS, TOKEN
from client_manager.base import ClientManger
from db.create_table import init_database


async def main():
    print("##### CREATE DATABASE #####")
    init_database(SUDO_IDS)
    print("##### RUN BOT  #####")
    bot = ClientManger(name="ftag", api_hash=API_HASH, api_id=API_ID, bot_token=TOKEN)
    await bot.start()
    print("##### BOT IS UP #####")

    # bot.start() only connects and returns - without idle() the process
    # would exit immediately after starting. idle() blocks here until the
    # process receives a stop signal (CTRL+C / SIGTERM), which is what
    # actually keeps the bot listening for updates.
    await idle()

    await bot.stop()
    print("##### BOT STOPPED #####")


if __name__ == "__main__":
    # asyncio.run() creates the loop, runs main() to completion, and makes
    # sure that any exception raised during startup (bad DB credentials,
    # bad TOKEN, etc.) is actually printed instead of being silently
    # swallowed, which previously made the bot look like it "just doesn't
    # start" with no visible error.
    asyncio.run(main())
