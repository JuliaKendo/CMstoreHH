import sys
import asyncio
import logging

from environs import Env
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Text
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import STATE_STOPPED

from exceptions import handle_tg_errors
from google_sheets import get_resume_ids
from hh_resumes import get_job_search_statuses

env = Env()
env.read_env()

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
logger = logging.getLogger('CMstoreHH')


async def start_job_by_interval(bot: Bot, message: types.Message):

    result = get_job_search_statuses(
        get_resume_ids(
            env('GOOGLE_SPREADSHEET_ID'),
            env('GOOGLE_RANGE_NAME')
        ),
        env("REDIS_SERVER")
    )

    if result:
        await bot.send_message(message.chat['id'], '\n'.join(result))


async def cmd_confirm_start(message: types.Message):
    if scheduler.state == STATE_STOPPED:
        scheduler.start()
        return
    scheduler.resume()        


async def cmd_confirm_stop(message: types.Message):
    await message.answer(
        'Мониторинг остановлен',
        parse_mode=types.ParseMode.MARKDOWN,
        reply_markup=types.ReplyKeyboardRemove()
    )
    scheduler.shutdown(wait=True)


async def cmd_start(message: types.Message):  
    buttons = [[
        types.KeyboardButton(text='Запустить'),
        types.KeyboardButton(text='Остановить')
    ],]
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await message.answer(
        'Запустить мониторинг hh.ru:',
        parse_mode=types.ParseMode.MARKDOWN,
        reply_markup=keyboard
    )

    if not scheduler.get_jobs():
        scheduler.add_job(
            start_job_by_interval,
            trigger='interval',
            seconds=60,
            kwargs={'bot': message.bot, 'message': message}
        )


def register_handlers_common(dp: Dispatcher):
    # Регистрация общих обработчиков
    dp.register_message_handler(cmd_start, commands=['start'], state='*')
    dp.register_message_handler(cmd_confirm_start, Text(equals="Запустить", ignore_case=True), state="*")      
    dp.register_message_handler(cmd_confirm_stop, Text(equals="Остановить", ignore_case=True), state="*")      


async def set_commands(bot: Bot):
    commands = [
        types.BotCommand(command="/start", description="Запустить бота"),
    ]
    await bot.set_my_commands(commands)


async def main():

    logging.basicConfig(
        filename='CMstoreHH.log',
        filemode='w',
        level=logging.DEBUG,
        format='%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
    )

    bot = Bot(token=env("TG_TOKEN"))
    dp = Dispatcher(bot)

    await set_commands(bot)

    # Обработчики логики бота
    register_handlers_common(dp)

    # Обработчики ошибок
    dp.register_errors_handler(handle_tg_errors)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
        loop.close()
    except KeyboardInterrupt:
        sys.stderr.write('Bot shut down')
