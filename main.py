import logging

from environs import Env
from aiogram import Bot, Dispatcher, executor, types

from google_sheets import get_resume_ids
from hh_oauth import sign_in_hh
from hh_resumes import get_job_search_statuses

env = Env()
env.read_env()

bot = Bot(token=env("TG_TOKEN"))
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)


@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    with sign_in_hh() as access_token:
        job_search_statuses = get_job_search_statuses(
            access_token, get_resume_ids(
                spreadsheet_id = env('GOOGLE_SPREADSHEET_ID'),
                sheet_range = env('GOOGLE_RANGE_NAME')
            ), env("REDIS_SERVER")
        ) 
        await message.reply('\n'.join(job_search_statuses))


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
