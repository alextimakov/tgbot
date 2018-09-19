from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler)
import time
import calendar
import logging
from multiprocessing import Process
import src.dbhelper as db_hp
import src.config as config
from src.scripts import *
from src.shelve import *

channel_name = '@findaride'

updater = Updater(token=config.token)  # Токен API к Telegram
dp = updater.dispatcher

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Global vars:
START, MENU, SET_STATE, LOGIN, CHECK, NEWS, ATTACH, NO_ATTACH, SENT, ANSWER, RESULT, WHERE, ANSWER_MOD, ANSWER_USER = \
    range(14)
STATE = START
unique_token = 0


def start(bot, update):
    user = update.message.from_user
    auth = db_hp.SQLighter('db.sqlite')
    bot.send_message(chat_id=user.id, text=welcome_text['RU'])
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
    global unique_token
    unique_token = update.message.message_id
    logger.info("Меню вызвано пользователем {}.".format(user.first_name))
    update.message.reply_text(menu_text['RU'], reply_markup=reply_markup)
    return SET_STATE


def set_state(bot, update):
    global STATE
    STATE = SET_STATE
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
    uid = update.message.text.lower()
    auth = db_hp.SQLighter('db.sqlite')
    all_users = []
    all_bosses = []
    for i in range(len(auth.select_user())):
        all_users.extend(auth.select_user()[i])
    for i in range(len(auth.select_boss())):
        all_bosses.extend(auth.select_boss()[i])
    if auth.select_person(uid):
        if uid in all_users and uid in all_bosses:
            logger.info("Новый uid сотрудника-руководителя")
            auth.update_user(user.id, uid)
            auth.update_boss(user.id, uid)
        elif uid in all_users:
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
        bot.send_message(chat_id=update.message.chat_id, text=back2menu['RU'])
        return CHECK


# news procedure
def news(bot, update):
    user = update.message.from_user
    logger.info("%s начал писать новость с приложением", user.first_name)
    update.message.reply_text(attach_req['RU'])
    auth = db_hp.SQLighter('db.sqlite')
    boss_uid = auth.select_boss_id(user.id)
    if auth.select_boss_id(user.id):
        auth.update_news_start(id=unique_token, status=0, user_id=user.id, boss_id=boss_uid[0])
    else:
        bot.send_message(chat_id=update.message.chat_id, text=user_not_found['RU'])
    return ATTACH


# news with attachment
def send_photo(bot, update):
    user = update.message.from_user
    auth = db_hp.SQLighter('db.sqlite')
    logger.info("%s отправил фотографию", user.first_name)
    post_time = calendar.timegm(time.gmtime())
    caption = update.message.caption
    photo = str(update.message.photo[-1].file_id)
    auth.update_news_attach(attach=photo, key=unique_token)
    bot.send_message(chat_id=update.message.chat_id, text=attach_acq['RU'])
    if caption:
        boss_uid = auth.select_boss_id(user.id)[0]
        bot.send_message(chat_id=boss_uid, text=new_news['RU'])
        logger.info("%s отправил текст новости", user.first_name)
        auth.update_news_text(time=post_time, text=str(caption), key=unique_token)
        update.message.reply_text(news_acq['RU'])
        bot.send_message(update.message.chat.id, 'Новость успешно отправлена руководителю!')
        update.message.reply_text(back2menu['RU'])
        return MENU
    else:
        update.message.reply_text(news_req['RU'])
        return SENT


# news without attachment
def no_attachment(bot, update):
    user = update.message.from_user
    logger.info("{} начал писать новость без приложения.".format(user.first_name))
    bot.send_message(chat_id=update.message.chat_id, text=news_req['RU'])
    auth = db_hp.SQLighter('db.sqlite')
    boss_uid = auth.select_boss_id(user.id)
    if auth.select_boss_id(user.id):
        auth.update_news_start(id=unique_token, status=0, user_id=user.id, boss_id=boss_uid[0])
    else:
        bot.send_message(chat_id=update.message.chat_id, text=user_not_found['RU'])
    return SENT


def send_news(bot, update):
    user = update.message.from_user
    auth = db_hp.SQLighter('db.sqlite')
    boss_uid = auth.select_boss_id(user.id)[0]
    bot.send_message(chat_id=boss_uid, text=new_news['RU'])
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
    logger.info("Руководитель проверил обновления %s", user.first_name)  # руководитель заходит в согласование
    auth = db_hp.SQLighter('db.sqlite')
    user_uid = auth.select_user_id(boss=user.id)  # выбираем пользователей, которые являются руководителями
    number_answers = auth.count_news(boss_id=user.id, status=0)  # чтобы начать проверять с самой ранней новости
    if user_uid:  # для контроля, является ли пользователь руководителем и есть ли новости
        if number_answers > 0:  # доп проверка по пустым новостям
            answer_text = auth.check_news(user.id)[-1 * number_answers]
            if answer_text:
                checked_user = auth.select_id_by_news(text=answer_text[0])[0]
                bot.send_message(chat_id=user.id,
                                 text='Новость получена от {}'
                                 .format(auth.select_user_by_id(id=checked_user)[0]))
                bot.send_message(chat_id=user.id, text=''.join(answer_text[0]))
                if auth.fetch_file_id(text=answer_text[0])[0]:
                    bot.send_photo(chat_id=user.id, photo=str(auth.fetch_file_id(text=answer_text[0])[0]))
                else:
                    pass
                keyboard = [['ОК', 'Не ОК']]

                reply_markup = ReplyKeyboardMarkup(keyboard,
                                                   one_time_keyboard=True,
                                                   resize_keyboard=True)

                update.message.reply_text(text='Выберите ОК, если новость согласована', reply_markup=reply_markup)
                logger.info("1 шаг согласования - проверка")
                return RESULT
            else:
                bot.send_message(chat_id=user.id, text='Новость не содержит текста и приложений. Нажмите /cancel')
                logger.info("1 шаг согласования - пустая новость")
                return MENU
        else:
            bot.send_message(chat_id=user.id, text=answer_neg['RU'])
            logger.info("1 шаг согласования - нет новостей")
            return MENU
    else:
        bot.send_message(chat_id=user.id, text=answer_rights['RU'])
        return MENU


def answer_result(bot, update):
    user = update.message.from_user
    post_time = calendar.timegm(time.gmtime())
    auth = db_hp.SQLighter('db.sqlite')
    number_answers = auth.count_news(boss_id=user.id, status=0)
    answer_text = auth.check_news(user.id)[-1 * number_answers]
    checked_user = auth.select_id_by_news(text=answer_text[0])[0]
    logger.info("Ответ руководителя %s: %s", user.first_name, update.message.text)
    if update.message.text == 'ОК':
        logger.info("2 шаг согласования - OK")
        auth.update_news_status(status=1, text=answer_text[0])
        auth.update_answer_time(time=post_time, text=answer_text[0])
        bot.send_message(chat_id=user.id, text=answer_sent_mods['RU'])
        bot.send_message(chat_id=user.id, text=back2menu['RU'])
        bot.send_message(chat_id=checked_user, text=answer_sent_mods['RU'])
        if auth.fetch_file_id(text=answer_text[0])[0]:
            bot.send_photo(chat_id=channel_name, photo=str(auth.fetch_file_id(text=answer_text[0])[0]))
        else:
            pass
        bot.send_message(chat_id=channel_name, text=answer_text[0])
        return MENU
    else:
        logger.info("2 шаг согласования - else")
        keyboard = [['Модератор', 'Сотрудник']]

        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard=True,
                                           resize_keyboard=True)

        user = update.message.from_user
        logger.info("Меню модератора вызвано пользователем {}.".format(user.first_name))
        update.message.reply_text(
            text='Нажмите Модератор, если хотите изменить новость самостоятельно и сразу отправить её модератору\n'
                 'Нажмите Сотрудник, если хотите отправить комментарий сотруднику', reply_markup=reply_markup)
        return WHERE


def answer_where(bot, update):
    user = update.message.from_user
    if update.message.text == 'Модератор':
        bot.send_message(chat_id=user.id, text='Введите изменённый текст новости для отправки модератору')
        return ANSWER_MOD
    else:
        bot.send_message(chat_id=user.id, text='Введите изменённый текст новости для отправки сотруднику')
        return ANSWER_USER


def answer_mod(bot, update):
    user = update.message.from_user
    post_time = calendar.timegm(time.gmtime())
    auth = db_hp.SQLighter('db.sqlite')
    number_answers = auth.count_news(boss_id=user.id, status=0)
    answer_text = auth.check_news(user.id)[-1 * number_answers]
    checked_user = auth.select_id_by_news(text=answer_text[0])[0]
    auth.update_news_answer(answer=answer_text[0], text=answer_text[0])
    auth.update_answer_time(time=post_time, text=answer_text[0])
    auth.update_news_status(status=1, text=answer_text[0])
    auth.update_news_text_only(new_text=update.message.text, old_text=answer_text[0])
    bot.send_message(chat_id=user.id, text=answer_sent_mods['RU'])
    bot.send_message(chat_id=user.id, text='Непроверенных новостей: {}'
                     .format(auth.count_news(boss_id=user.id, status=0)))
    bot.send_message(chat_id=user.id, text=back2menu['RU'])
    bot.send_message(chat_id=checked_user, text=answer_sent_mods['RU'])
    if auth.fetch_file_id(text=update.message.text)[0]:
        bot.send_photo(chat_id=channel_name, photo=str(auth.fetch_file_id(text=update.message.text)[0]))
    else:
        pass
    bot.send_message(chat_id=channel_name, text=update.message.text)
    return MENU


def answer_user(bot, update):
    user = update.message.from_user
    post_time = calendar.timegm(time.gmtime())
    auth = db_hp.SQLighter('db.sqlite')
    number_answers = auth.count_news(boss_id=user.id, status=0)
    answer_text = auth.check_news(user.id)[-1 * number_answers]
    checked_user = auth.select_id_by_news(text=answer_text[0])[0]
    auth.update_news_answer(answer=update.message.text, text=answer_text[0])
    auth.update_answer_time(time=post_time, text=answer_text[0])
    bot.send_message(chat_id=checked_user, text=answer_acq_user['RU'])
    bot.send_message(chat_id=checked_user, text=update.message.text)
    bot.send_message(chat_id=user.id, text=answer_sent_user['RU'])
    bot.send_message(chat_id=user.id, text='Непроверенных новостей: {}'
                     .format(auth.count_news(boss_id=user.id, status=0)))
    return MENU


# def answer(bot, update):
#     user = update.message.from_user
#     logger.info("Руководитель проверил обновления %s", user.first_name)  # руководитель заходит в согласование
#     auth = db_hp.SQLighter('db.sqlite')
#     user_uid = auth.select_user_id(boss=user.id)  # выбираем пользователей, которые являются руководителями
#     number_answers = auth.count_news(boss_id=user.id, status=0)  # чтобы начать проверять с самой ранней новости
#     if user_uid and number_answers > 0:  # для контроля, является ли пользователь руководителем и есть ли новости
#         answer_text = auth.check_news(user.id)[-1 * number_answers]
#         if answer_text:  # доп проверка по пустым новостям
#             checked_user = auth.select_id_by_news(text=answer_text[0])[0]
#             bot.send_message(chat_id=user.id, text=answer_pos['RU'])
#             bot.send_message(chat_id=user.id,
#                              text='Новость получена от {}'
#                              .format(auth.select_user_by_id(id=checked_user)[0]))
#             bot.send_message(chat_id=user.id, text=''.join(answer_text[0]))
#             if auth.fetch_file_id(text=answer_text[0])[0]:
#                 bot.send_photo(chat_id=user.id, photo=str(auth.fetch_file_id(text=answer_text[0])[0]))
#             else:
#                 pass
#             logger.info("1 шаг согласования - проверка")
#             return RESULT
#         else:
#             bot.send_message(chat_id=user.id, text=answer_neg['RU'])
#             logger.info("1 шаг согласования - нет новостей")
#             return MENU
#     else:
#         bot.send_message(chat_id=user.id, text=answer_rights['RU'])
#         return MENU


# def answer_result(bot, update):
#     user = update.message.from_user
#     post_time = calendar.timegm(time.gmtime())
#     auth = db_hp.SQLighter('db.sqlite')
#     number_answers = auth.count_news(boss_id=user.id, status=0)
#     answer_text = auth.check_news(user.id)[-1 * number_answers]
#     checked_user = auth.select_id_by_news(text=answer_text[0])[0]
#     logger.info("Ответ руководителя %s: %s", user.first_name, update.message.text)
#     if str(update.message.text) == 'ОК' or str(update.message.text) == 'OK':
#         logger.info("2 шаг согласования - OK")
#         auth.update_news_status(status=1, text=answer_text[0])
#         auth.update_answer_time(time=post_time, text=answer_text[0])
#         bot.send_message(chat_id=user.id, text=answer_sent_mods['RU'])
#         bot.send_message(chat_id=user.id, text=back2menu['RU'])
#         bot.send_message(chat_id=checked_user, text=answer_sent_mods['RU'])
#         bot.send_message(chat_id=channel_name, text=answer_text[0])
#         if auth.fetch_file_id(text=answer_text[0])[0]:
#             bot.send_photo(chat_id=channel_name, photo=str(auth.fetch_file_id(text=answer_text[0])[0]))
#         else:
#             pass
#         return MENU
#     else:
#         logger.info("2 шаг согласования - else")
#         auth.update_news_answer(answer=update.message.text, text=answer_text[0])
#         auth.update_answer_time(time=post_time, text=answer_text[0])
#         bot.send_message(chat_id=user.id, text=answer_sent_choice['RU'])
#         return WHERE


# def answer_where(bot, update):
#     user = update.message.from_user
#     auth = db_hp.SQLighter('db.sqlite')
#     answer_time = auth.select_answer_time(boss_id=user.id)
#     time_list = sorted([i[0] for i in answer_time], reverse=True)
#     answer_text = auth.check_news_time(boss_id=user.id, answer_time=time_list[0])
#     comment = str(auth.check_answer(text=answer_text[0])[0])
#     checked_user = auth.select_id_by_news(text=answer_text[0])[0]
#     if str(update.message.text) == 'М' or str(update.message.text) == 'M':
#         auth.update_news_status(status=1, text=answer_text[0])
#         bot.send_message(chat_id=user.id, text=answer_sent_mods['RU'])
#         bot.send_message(chat_id=user.id, text=back2menu['RU'])
#         bot.send_message(chat_id=checked_user, text=answer_sent_mods['RU'])
#         bot.send_message(chat_id=channel_name, text=answer_text[0])
#         if auth.fetch_file_id(text=answer_text[0])[0]:
#             bot.send_photo(chat_id=channel_name, photo=str(auth.fetch_file_id(text=answer_text[0])[0]))
#         else:
#             pass
#     else:
#         bot.send_message(chat_id=checked_user, text=answer_acq_user['RU'])
#         bot.send_message(chat_id=checked_user, text=comment)
#         bot.send_message(chat_id=user.id, text=answer_sent_user['RU'])
#     return MENU

# general functions
FLAG = True


def callback(bot):
    while FLAG:
        time.sleep(60*60*24)
        auth = db_hp.SQLighter('db.sqlite')
        current_time = calendar.timegm(time.gmtime())
        user = auth.fetch_user_id_news()
        user_f = [user for user in user if len(str(user[0])) > 5]
        user_list = [user[0] for user in user_f]
        if user_list:
            rem_check = [user for user in user_list if (current_time - auth.check_time(user)[-1][0]) > (60*60*24*7)]
            if rem_check:
                for i in range(len(rem_check)):
                    bot.send_message(chat_id=rem_check[i], text=reminder_text['RU'])
                    logger.info("Новость написана давно %s", rem_check[i])
            else:
                logger.info("Все новости написаны недавно")
                pass
        else:
            logger.info("В базе нет пользователей!")
            pass
    pass


def cancel(bot, update):
    user = update.message.from_user
    logger.info("Пользователь {} прервал диалог.".format(user.first_name))
    update.message.reply_text(text=cancel_text['RU'],
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    # Add conversation handler with predefined states:
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('menu', menu)],

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

            WHERE: [MessageHandler(Filters.text, answer_where)],

            ANSWER_MOD: [MessageHandler(Filters.text, answer_mod)],

            ANSWER_USER: [MessageHandler(Filters.text, answer_user)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conversation_handler)

    # Log all errors:
    dp.add_error_handler(error)


if __name__ == '__main__':
    main()
    bot = updater.bot
    p = Process(target=callback, args=(bot, ))
    p.start()
    updater.start_polling(clean=False)
