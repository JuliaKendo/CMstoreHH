import sys
import asyncio
import logging
import rollbar

from environs import Env
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.filters import Text
from aiogram.utils import exceptions
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from google_sheets import get_resume_ids
from hh_resumes import get_job_search_statuses

env = Env()
env.read_env()

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
logger = logging.getLogger('CMstoreHH')

async def tg_errors_handler(update, exception):
    """
    Exceptions handler. Catches all exceptions within task factory tasks.
    :param dispatcher:
    :param update:
    :param exception:
    :return: stdout logging
    """

    if isinstance(exception, exceptions.CantDemoteChatCreator):
        logging.error("Can't demote chat creator")
        rollbar.report_exc_info()
        return True

    if isinstance(exception, exceptions.TerminatedByOtherGetUpdates):
        logging.error('Terminated by other getUpdates request; Make sure that only one bot instance is running')
        rollbar.report_exc_info()
        return True

    if isinstance(exception, exceptions.MessageNotModified):
        logging.error('Message is not modified')
        rollbar.report_exc_info()
        return True

    if isinstance(exception, exceptions.MessageCantBeDeleted):
        logging.error('Message cant be deleted')
        rollbar.report_exc_info()
        return True

    if isinstance(exception, exceptions.MessageToDeleteNotFound):
        logging.error('Message to delete not found')
        rollbar.report_exc_info()
        return True

    if isinstance(exception, exceptions.MessageTextIsEmpty):
        logging.error('MessageTextIsEmpty')
        rollbar.report_exc_info()
        return True

    if isinstance(exception, exceptions.Unauthorized):
        logging.error(f'Unauthorized: {exception}')
        rollbar.report_exc_info()
        return True

    if isinstance(exception, exceptions.InvalidQueryID):
        logging.error(f'InvalidQueryID: {exception} \nUpdate: {update}')
        rollbar.report_exc_info()
        return True

    if isinstance(exception, exceptions.TelegramAPIError):
        logging.error(f'TelegramAPIError: {exception} \nUpdate: {update}')
        rollbar.report_exc_info()
        return True
    if isinstance(exception, exceptions.RetryAfter):
        logging.error(f'RetryAfter: {exception} \nUpdate: {update}')
        rollbar.report_exc_info()
        return True
    if isinstance(exception, exceptions.CantParseEntities):
        logging.error(f'CantParseEntities: {exception} \nUpdate: {update}')
        rollbar.report_exc_info()
        return True

    logging.error(f'Update: {update} \n{exception}')
    rollbar.report_exc_info()


async def start_job_by_interval(bot: Bot, message: types.Message):
    resume_ids = get_resume_ids(env('GOOGLE_SPREADSHEET_ID'), env('GOOGLE_RANGE_NAME'))
    
    if not resume_ids:
        logging.error('error getting user ids or set up google spreadsheet authentication')
        return

    result = get_job_search_statuses(resume_ids, env("REDIS_SERVER"))

    if not isinstance(result, list):
        logging.error(result)
        return

    await bot.send_message(message.chat['id'], '\n'.join(result))


async def cmd_confirm_start(message: types.Message):
    scheduler.start()


async def cmd_confirm_stop(message: types.Message):
    await message.answer(
        'Мониторинг остановлен',
        parse_mode=types.ParseMode.MARKDOWN,
        reply_markup=types.ReplyKeyboardRemove()
    )
    scheduler.shutdown()


async def cmd_start(message: types.Message):  
    buttons = [
        [
            types.KeyboardButton(text='Запустить'),
            types.KeyboardButton(text='Остановить')
        ],
    ]
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

    scheduler.add_job(start_job_by_interval, trigger='interval', seconds=60, kwargs={'bot': message.bot, 'message': message})


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
    dp.register_errors_handler(tg_errors_handler)

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
