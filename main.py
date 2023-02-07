import logging

from environs import Env
from aiogram import Bot, Dispatcher, executor, types

from google_sheets import get_resume_ids
from hh_resumes import get_job_search_statuses

env = Env()
env.read_env()

bot = Bot(token=env("TG_TOKEN"))
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    resume_ids = get_resume_ids(env('GOOGLE_SPREADSHEET_ID'), env('GOOGLE_RANGE_NAME'))
    
    if not resume_ids:
        await message.reply('set up google spreadsheet authentication')
        return

    result = get_job_search_statuses(resume_ids, env("REDIS_SERVER"))

    if not isinstance(result, list):
        await message.reply(result)
        return

    await message.reply('\n'.join(result))
      

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
