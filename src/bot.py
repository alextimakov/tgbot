from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler)
import time
import calendar
import src.config as config
import src.db as db
from src.scripts import *
import logging
# from multiprocessing import Pool
import src.dbhelper as db_hp

channel_name = '@findaride'

updater = Updater(config.token)  # Токен API к Telegram
dp = updater.dispatcher
j = updater.job_queue

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)


# Global vars:
START, MENU, SET_STATE, LOGIN, CHECK, NEWS, ATTACH, NO_ATTACH, SENT, ANSWER, RESULT = range(11)
STATE = START
unique_token = 0


def start(bot, update):
    user = update.message.from_user
    global unique_token
    unique_token = update.message.message_id
    auth = db_hp.SQLighter('db.sqlite')
    all_ids = []
    for i in range(auth.count_rows()):
        all_ids.extend([auth.select_all()[i][2], auth.select_all()[i][3]])
    for i in range(len(all_ids)):
        if user.id in all_ids:
            bot.send_message(chat_id=update.message.chat_id, text=login_check_init_suc['RU'])
            return MENU
        else:
            login(bot, update)
            return CHECK


def menu(bot, update):
    keyboard = [[login_menu['RU'], news_menu['RU']],
                [answer_menu['RU'], attach_menu['RU']]]

    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard=True,
                                       resize_keyboard=True)

    user = update.message.from_user
    logger.info("Меню вызвано пользователем {}.".format(user.first_name))
    update.message.reply_text(menu_text['RU'], reply_markup=reply_markup)
    return SET_STATE


def set_state(bot, update):
    global STATE
    if update.message.text == login_menu['RU']:
        STATE = LOGIN
        login(bot, update)
        return CHECK
    elif update.message.text == attach_menu['RU']:
        STATE = NEWS
        news(bot, update)
        return ATTACH
    elif update.message.text == answer_menu['RU']:
        STATE = ANSWER
        answer(bot, update)
        return RESULT
    elif update.message.text == news_menu['RU']:
        STATE = NO_ATTACH
        no_attachment(bot, update)
        return SENT
    else:
        STATE = MENU
        return MENU


# login procedure
def login(bot, update):
    user = update.message.from_user
    logger.info("{} пытается авторизоваться.".format(user.first_name))
    update.message.reply_text(login_req['RU'])
    return CHECK


def check(bot, update):
    user = update.message.from_user
    logger.info("{} отправил логин.".format(user.first_name))
    update.message.reply_text(login_acq['RU'])
    uid = update.message.text.lower()
    auth = db_hp.SQLighter('db.sqlite')
    all_users = []
    all_bosses = []
    for i in range(len(auth.select_user())):
        all_users.extend(auth.select_user()[i])
    for i in range(len(auth.select_boss())):
        all_bosses.extend(auth.select_boss()[i])
    if auth.select_person(uid):
        if uid in all_users:
            logger.info("Новый uid сотрудника")
            auth.update_user(user.id, uid)
        elif uid in all_bosses:
            logger.info("Новый uid руководителя")
            auth.update_boss(user.id, uid)
        else:
            pass

        bot.send_message(chat_id=update.message.chat_id, text=login_check_suc['RU'])
        return MENU
    else:
        bot.send_message(chat_id=update.message.chat_id, text=login_check_fail['RU'])
        return CHECK


# news procedure
def news(bot, update):
    user = update.message.from_user
    logger.info("%s начал писать новость", user.first_name)
    update.message.reply_text(attach_req['RU'])
    auth = db_hp.SQLighter('db.sqlite')
    boss_uid = auth.select_boss_id(user.id)[0]
    auth.update_news_start(values=[unique_token, 0, user.id, boss_uid])
    return


# news with attachment
def send_photo(bot, update):
    user = update.message.from_user
    auth = db_hp.SQLighter('db.sqlite')
    boss_uid = auth.select_boss_id(user.id)[0]
    bot.send_photo(chat_id=boss_uid, photo=update.message.photo[-1].file_id)
    logger.info("%s отправил фотографию", user.first_name)
    photo = str(update.message.photo[-1].file_id)
    auth.update_news_attach(attach=photo, key=unique_token)
    bot.send_message(chat_id=update.message.chat_id, text=attach_acq['RU'])
    update.message.reply_text(news_req['RU'])
    return SENT


# news without attachment
def no_attachment(bot, update):
    user = update.message.from_user
    logger.info("Информация о боте запрошена пользователем {}.".format(user.first_name))
    bot.send_message(chat_id=update.message.chat_id, text=news_req['RU'])
    return SENT


def send_news(bot, update):
    user = update.message.from_user
    auth = db_hp.SQLighter('db.sqlite')
    boss_uid = auth.select_boss_id(user.id)[0]
    bot.send_message(chat_id=boss_uid, text=update.message.text)
    logger.info("%s отправил текст новости", user.first_name)
    post_time = calendar.timegm(time.gmtime())
    auth.update_news_text(time=post_time, text=update.message.text, key=unique_token)
    update.message.reply_text(news_acq['RU'])
    bot.send_message(update.message.chat.id, 'Новость успешно отправлена руководителю!')
    update.message.reply_text(back2menu['RU'])
    return MENU


# answer procedure
def answer(bot, update):
    user = update.message.from_user
    logger.info("Руководитель проверил обновления %s", user.first_name)
    auth = db_hp.SQLighter('db.sqlite')
    boss_uid = auth.select_boss_id(user.id)
    number_answers = auth.count_news(boss_uid)
    for i in reversed(range(number_answers)):
        while i > 0:
            if auth.check_news(boss_uid)[-i:]:
                bot.send_message(chat_id=user.id, text=answer_pos['RU'])
                bot.send_message(chat_id=user.id, text=''.join(auth.check_news(boss_uid)[-i:]))
                i -= 1
                logger.info("1 шаг согласования - проверка")
                return RESULT
            else:
                bot.send_message(chat_id=user.id, text=answer_neg['RU'])
                logger.info("1 шаг согласования - нет новостей")
                return MENU
    return MENU

# def answer(bot, update):
#     user = update.message.from_user
#     logger.info("Руководитель проверил обновления %s", user.first_name)
#     base = news_base.loc[news_base['boss_id'] == user.id]
#     # add iterative check of status
#     if base['status'][-1:] is not False:
#         if not base['text'][-1:].empty:
#             bot.send_message(chat_id=user.id, text='Поставьте ОК если согласовано, '
#                                                    'напишите комментарий в противном случае')
#             bot.send_message(chat_id=user.id, text=''.join(base['text'][-1:]))
#             logger.info("1 шаг согласования")
#             return RESULT
#         else:
#             bot.send_message(chat_id=user.id, text='У вас нет прав для согласования. Вернитесь в /menu')
#             return MENU
#     else:
#         return MENU


def answer_result(bot, update):
    user = update.message.from_user
    auth = db_hp.SQLighter('db.sqlite')
    user_uid = auth.select_user_id(user.id)
    if str(update.message.text) == 'ОК':
        logger.info("2 шаг согласования - OK")
        bot.send_message(chat_id=channel_name, text=update.message.text)
    else:
        logger.info("2 шаг согласования - else")
        bot.send_message(chat_id=int(user_uid), text=update.message.text)
    # base['status'][-1:] = True
    logger.info("Ответ руководителя %s: %s", user.first_name, update.message.text)
    bot.send_message(chat_id=user.id, text=back2menu['RU'])
    return MENU


# def answer_result(bot, update):
#     user = update.message.from_user
#     last = db.setup('db2.csv')
#     base = last.loc[last['boss_id'] == user.id]
#     if str(update.message.text) == 'ОК':
#         logger.info("2 шаг согласования OK")
#         bot.send_message(chat_id=channel_name, text=update.message.text)
#     else:
#         logger.info("2 шаг согласования - else")
#         bot.send_message(chat_id=int(base['user_id'][-1:]), text=update.message.text)
#     # base['status'][-1:] = True
#     logger.info("Ответ руководителя %s: %s", user.first_name, update.message.text)
#     bot.send_message(chat_id=user.id, text=back2menu['RU'])
#     return MENU

# general functions
def callback_alarm(bot, job):
    last = db.setup('db2.csv')
    current_time = calendar.timegm(time.gmtime())
    rem_check = int(last['time'].loc[last['user_id'] == job.context][-1:])
    if int(current_time - rem_check) >= 120:
        logger.info("Проверено, как давно была написана новость")
        bot.send_message(chat_id=int(last['user_id'].loc[last['user_id'] == job.context][-1:]),
                         text=reminder_text['RU'])


def callback_timer(bot, update, job_queue):
    bot.send_message(chat_id=update.message.chat_id, text='Пройдите, пожалуйста, в /menu')
    job_queue.run_repeating(callback_alarm, 20, context=update.message.chat_id)


def help(bot, update):
    user = update.message.from_user
    logger.info("Пользователь {} просит помочь".format(user.first_name))
    update.message.reply_text(text='Напишите сообщение',
                              reply_markup=ReplyKeyboardRemove())


def cancel(bot, update):
    user = update.message.from_user
    logger.info("ПОльзователь {} прервал диалог.".format(user.first_name))
    update.message.reply_text(text='Перезапуск диалога',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    # create handlers
    timer_handler = CommandHandler('timer', callback_timer, pass_job_queue=True)

    # add handlers
    dp.add_handler(timer_handler)

    # Add conversation handler with predefined states:
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            MENU: [CommandHandler('menu', menu)],

            SET_STATE: [RegexHandler(
                        '^({}|{}|{}|{})$'.format(
                            login_menu['RU'], news_menu['RU'], answer_menu['RU'], attach_menu['RU']), set_state)],

            CHECK: [MessageHandler(Filters.text, check), CommandHandler('menu', menu)],

            ATTACH: [MessageHandler(Filters.photo, send_photo), CommandHandler('send_news', send_news)],

            NO_ATTACH: [MessageHandler(Filters.text, no_attachment), CommandHandler('send_news', send_news)],

            SENT: [MessageHandler(Filters.text, send_news), CommandHandler('menu', menu)],

            RESULT: [MessageHandler(Filters.text, answer_result)],
        },

        fallbacks=[CommandHandler('cancel', cancel),
                   CommandHandler('help', help)]
    )

    dp.add_handler(conversation_handler)

    # Log all errors:
    dp.add_error_handler(error)


if __name__ == '__main__':
    main()
    updater.start_polling(clean=True)
    updater.idle()
