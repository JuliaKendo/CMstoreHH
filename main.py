import sys
import asyncio
import logging
import configparser

from environs import Env
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.base import STATE_STOPPED

from google_sheets import get_resume_ids
from hh_resumes import get_job_search_statuses
from exceptions import handle_tg_errors

env = Env()
env.read_env()

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
logger = logging.getLogger('CMstoreHH')


class AccessingMiddleware(BaseMiddleware):

    def __init__(self):
        super(AccessingMiddleware, self).__init__()

    def get_accessed_ids(self):

        parser = configparser.ConfigParser()
        parser.read('accessed.ini')

        ids = parser['DEFAULT'].get('ids')
        if ids:
            return ids.split(';')
        return []

    async def on_process_message(self, message: types.Message, data: dict):
        accessed_ids = self.get_accessed_ids()
        if not str(message.chat.id) in accessed_ids:
            await message.reply('Forbidden access')
            raise CancelHandler()


async def start_job_by_interval(bot: Bot, message: types.Message):

    tg_group_id = env('TG_GROUP_ID')
    result, employees_with_unavailable_statuses = get_job_search_statuses(
        get_resume_ids(
            env('GOOGLE_SPREADSHEET_ID'),
            env('GOOGLE_RANGE_NAME')
        ),
        env("REDIS_SERVER")
    )

    if employees_with_unavailable_statuses:
        logger.exception(
            f'employees with unavailable statuses: {",".join(employees_with_unavailable_statuses)}'
        )

    if result:
        await bot.send_message(tg_group_id, '\n'.join(result))


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

    # Регистрируем мидлваре
    dp.middleware.setup(AccessingMiddleware())

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
    except (KeyboardInterrupt, SystemExit):
        sys.stderr.write('Bot shut down')
