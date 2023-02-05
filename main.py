import logging

from environs import Env
from aiogram import Bot, Dispatcher, executor, types

env = Env()
env.read_env()

bot = Bot(token=env("TG_TOKEN"))
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    await message.reply("CMstoreHH")


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
