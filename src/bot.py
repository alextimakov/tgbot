from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler)
from telegram.utils import request
import time
import calendar
import logging
import json
from multiprocessing import Process
import src.dbhelper as db
import src.config as config
from src.scripts import *
import src.shelve as sh

# временное решение - все новости идут на согласование модератору
channel_name = config.channel_name

updater = Updater(token=config.token, request_kwargs=config.REQUEST_KWARGS)
dp = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global vars:
unique_token = 0


def start(bot, update):
    user = update.message.from_user
    auth = db.SQLighter('db.sqlite')
    if auth.select_cond('user_id', 'user_boss', 'user_id', user.id):  # проверка первичной авторизации
        bot.send_message(chat_id=user.id, text=login_check_repeat['RU'])
        state = sh.get_current_state(sh.db_name, user.id)
        logger.info("Пользователь {} в состоянии {}".format(user.id, int(state)))
        # state control
        if int(state) == int(sh.States.LOGIN.value):
            bot.send_message(chat_id=user.id, text=state_auth['RU'])
            login(bot, update)
            return sh.States.CHECK
        elif int(state) == int(sh.States.NEWS.value):
            bot.send_message(chat_id=user.id, text=state_news['RU'])
            news(bot, update)
            return sh.States.ATTACH
        elif int(state) == int(sh.States.NO_ATTACH.value):
            bot.send_message(chat_id=user.id, text=state_no_attach['RU'])
            no_attachment(bot, update)
            return sh.States.SENT
        elif int(state) == int(sh.States.ANSWER.value):
            bot.send_message(chat_id=user.id, text=state_answer['RU'])
            answer(bot, update)
            return sh.States.RESULT
        else:
            bot.send_message(chat_id=user.id, text=login_check_init_suc['RU'])
            return sh.States.MENU
    else:
        bot.send_message(chat_id=update.message.chat_id, text=user_not_found['RU'])
        login(bot, update)
        return sh.States.CHECK


def menu(bot, update):
    keyboard = [[login_menu['RU'], news_menu['RU']],
                [answer_menu['RU'], attach_menu['RU']]]

    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard=True,
                                       resize_keyboard=True)

    user = update.message.from_user
    logger.info("Меню вызвано пользователем {}.".format(user.id))
    sh.set_state(sh.db_name, user.id, sh.States.MENU.value)
    auth = db.SQLighter('db.sqlite')
    if auth.select_cond('user_id', 'user_boss', 'user_id', user.id):
        update.message.reply_text(menu_text['RU'], reply_markup=reply_markup)
        return sh.States.SET_STATE
    else:
        bot.send_message(chat_id=user.id, text=user_init_auth['RU'])
        login(bot, update)
        return sh.States.CHECK


def set_state(bot, update):
    user = update.message.from_user
    sh.set_state(sh.db_name, user.id, sh.States.SET_STATE.value)
    if update.message.text == login_menu['RU']:
        login(bot, update)
        return sh.States.CHECK
    elif update.message.text == attach_menu['RU']:
        news(bot, update)
        return sh.States.ATTACH
    elif update.message.text == answer_menu['RU']:
        answer(bot, update)
        return sh.States.RESULT
    elif update.message.text == news_menu['RU']:
        no_attachment(bot, update)
        return sh.States.SENT
    else:
        sh.set_state(sh.db_name, user.id, sh.States.MENU.value)
        return sh.States.MENU


# auth procedure
def login(bot, update):
    user = update.message.from_user
    logger.info("{} пытается авторизоваться.".format(user.id))
    sh.set_state(sh.db_name, user.id, sh.States.LOGIN.value)
    bot.send_message(chat_id=user.id, text=login_req['RU'])
    return sh.States.CHECK


def check(bot, update):
    user = update.message.from_user
    logger.info("{} отправил логин.".format(user.id))
    sh.set_state(sh.db_name, user.id, sh.States.CHECK.value)
    uid = update.message.text.lower()
    auth = db.SQLighter('db.sqlite')
    all_users, all_bosses = [], []
    for i in range(len(auth.select_no_cond('user', 'user_boss'))):
        all_users.extend([auth.select_no_cond('user', 'user_boss')[i][0]])
    for i in range(len(auth.select_no_cond('boss', 'user_boss'))):
        all_bosses.extend([auth.select_no_cond('boss', 'user_boss')[i][0]])
    if auth.select_person(uid):
        if uid in all_users and uid in all_bosses:
            logger.info("Новый uid сотрудника-руководителя")
            auth.update_cond('user_boss', 'user_id', user.id, 'user', uid)
            auth.update_cond('user_boss', 'boss_id', user.id, 'boss', uid)
        elif uid in all_users:
            logger.info("Новый uid сотрудника")
            auth.update_cond('user_boss', 'user_id', user.id, 'user', uid)
        elif uid in all_bosses:
            logger.info("Новый uid руководителя")
            auth.update_cond('user_boss', 'boss_id', user.id, 'boss', uid)
        else:
            pass

        bot.send_message(chat_id=update.message.chat_id, text=login_check_suc['RU'])
        return sh.States.MENU
    else:
        bot.send_message(chat_id=update.message.chat_id, text=login_check_fail['RU'])
        return sh.States.CHECK


# news procedure
def news(bot, update):
    user = update.message.from_user
    logger.info("%s начал писать новость с приложением", user.id)
    sh.set_state(sh.db_name, user.id, sh.States.NEWS.value)
    auth = db.SQLighter('db.sqlite')
    if auth.select_cond('boss_id', 'user_boss', 'user_id', user.id)[0][0]:  # есть ли в базе руководитель юзера
        boss_uid = auth.select_cond('boss_id', 'user_boss', 'user_id', user.id)[0][0]
        global unique_token
        unique_token = update.message.message_id
        bot.send_message(chat_id=update.message.chat_id, text=attach_req['RU'])
        auth.insert_news_start(unique_id=unique_token, status=0, user_id=user.id, boss_id=boss_uid)
    else:
        bot.send_message(chat_id=update.message.chat_id, text=boss_not_found['RU'])
    return sh.States.ATTACH


# news with attachment
def send_photo(bot, update):
    user = update.message.from_user
    auth = db.SQLighter('db.sqlite')
    logger.info("%s отправил фотографию", user.id)
    sh.set_state(sh.db_name, user.id, sh.States.ATTACH.value)
    photo = str(update.message.photo[-1].file_id)
    auth.update_cond('news_base', 'file_id', photo, 'id', unique_token)
    bot.send_message(chat_id=user.id, text=attach_acq['RU'])
    post_time = calendar.timegm(time.gmtime())
    caption = update.message.caption
    if caption and len(caption) < 200:
        logger.info("%s отправил текст в caption", user.id)
        auth.update_cond('news_base', 'time', post_time, 'id', unique_token)
        auth.update_cond('news_base', 'news_text', str(caption), 'id', unique_token)
        boss_uid = auth.select_cond('boss_id', 'user_boss', 'user_id', user.id)[0][0]
        bot.send_message(chat_id=boss_uid, text=new_news['RU'])
        bot.send_message(chat_id=user.id, text=news_acq['RU'])
        bot.send_message(chat_id=user.id, text=news_sent['RU'])
        bot.send_message(chat_id=user.id, text=back2menu['RU'])
        return sh.States.MENU
    else:
        bot.send_message(chat_id=user.id, text=news_req['RU'])
        return sh.States.SENT


# news without attachment
def no_attachment(bot, update):
    user = update.message.from_user
    logger.info("{} начал писать новость без приложения.".format(user.id))
    sh.set_state(sh.db_name, user.id, sh.States.NO_ATTACH.value)
    auth = db.SQLighter('db.sqlite')
    if auth.select_cond('boss_id', 'user_boss', 'user_id', user.id)[0][0]:  # есть ли в базе руководитель юзера
        boss_uid = auth.select_cond('boss_id', 'user_boss', 'user_id', user.id)[0][0]
        global unique_token
        unique_token = update.message.message_id
        bot.send_message(chat_id=update.message.chat_id, text=news_req['RU'])
        auth.insert_news_start(unique_id=unique_token, status=0, user_id=user.id, boss_id=boss_uid)
    else:
        bot.send_message(chat_id=update.message.chat_id, text=boss_not_found['RU'])
    return sh.States.SENT


def send_news(bot, update):
    user = update.message.from_user
    auth = db.SQLighter('db.sqlite')
    post_time = calendar.timegm(time.gmtime())
    boss_uid = auth.select_cond('boss_id', 'user_boss', 'user_id', user.id)[0][0]
    logger.info("%s отправил текст новости", user.id)
    sh.set_state(sh.db_name, user.id, sh.States.SENT.value)
    auth.update_cond('news_base', 'time', post_time, 'id', unique_token)
    auth.update_cond('news_base', 'news_text', update.message.text, 'id', unique_token)
    bot.send_message(chat_id=boss_uid, text=new_news['RU'])
    bot.send_message(chat_id=user.id, text=news_acq['RU'])
    bot.send_message(chat_id=user.id, text=news_sent['RU'])
    bot.send_message(chat_id=user.id, text=back2menu['RU'])
    return sh.States.MENU


# answer procedure
def answer(bot, update):
    user = update.message.from_user
    logger.info("Руководитель проверил обновления %s", user.id)  # руководитель заходит в согласование
    sh.set_state(sh.db_name, user.id, sh.States.ANSWER.value)
    auth = db.SQLighter('db.sqlite')
    user_uid = auth.select_cond('user_id', 'user_boss', 'boss_id', user.id)
    if user_uid:  # является ли пользователь руководителем
        number_answers = len(auth.check_news(boss_id=user.id))  # чтобы начать проверять с самой ранней новости
        if number_answers > 0:  # проверка по пустым новостям
            answer_text = auth.check_news(user.id)[-1 * number_answers]
            if answer_text[0]:
                checked_user = auth.select_cond('user_id', 'news_base', 'news_text', answer_text[0])[0][0]
                bot.send_message(chat_id=user.id,
                                 text='Новость получена от {}'
                                 .format(auth.select_cond('user', 'user_boss', 'user_id', checked_user)[0][0]))
                bot.send_message(chat_id=user.id, text=''.join(answer_text[0]))
                if auth.select_cond('file_id', 'news_base', 'news_text', answer_text[0])[0][0]:
                    photo = str(auth.select_cond('file_id', 'news_base', 'news_text', answer_text[0])[0][0])
                    bot.send_photo(chat_id=user.id, photo=photo)
                else:
                    pass
                keyboard = [['ОК', 'Не ОК']]

                reply_markup = ReplyKeyboardMarkup(keyboard,
                                                   one_time_keyboard=True,
                                                   resize_keyboard=True)

                update.message.reply_text(text=press_ok['RU'], reply_markup=reply_markup)
                logger.info("1 шаг согласования - проверка")
                return sh.States.RESULT
            else:
                bot.send_message(chat_id=user.id, text=news_null['RU'])
                logger.info("1 шаг согласования - пустая новость")
                return sh.States.MENU
        else:
            bot.send_message(chat_id=user.id, text=answer_neg['RU'])
            logger.info("1 шаг согласования - нет новостей")
            return sh.States.MENU
    else:
        bot.send_message(chat_id=user.id, text=answer_rights['RU'])
        return sh.States.MENU


def answer_result(bot, update):
    user = update.message.from_user
    auth = db.SQLighter('db.sqlite')
    post_time = calendar.timegm(time.gmtime())
    number_answers = len(auth.check_news(boss_id=user.id))
    if number_answers > 0:
        answer_text = auth.check_news(user.id)[-1 * number_answers]
        checked_user = auth.select_cond('user_id', 'news_base', 'news_text', answer_text[0])[0][0]
        logger.info("Ответ руководителя %s: %s", user.id, update.message.text)
        sh.set_state(sh.db_name, user.id, sh.States.RESULT.value)
        if update.message.text == 'ОК':
            logger.info("2 шаг согласования - OK")
            auth.update_cond('news_base', 'status', 1, 'news_text', answer_text[0])
            auth.update_cond('news_base', 'answer_time', post_time, 'news_text', answer_text[0])
            bot.send_message(chat_id=user.id, text=answer_sent_mods['RU'])
            bot.send_message(chat_id=user.id, text='Непроверенных новостей: {}'
                             .format(len(auth.check_news(boss_id=user.id))))
            bot.send_message(chat_id=user.id, text=back2menu['RU'])
            bot.send_message(chat_id=checked_user, text=answer_sent_mods['RU'])
            if auth.select_cond('file_id', 'news_base', 'news_text', answer_text[0])[0][0]:
                photo = str(auth.select_cond('file_id', 'news_base', 'news_text', answer_text[0])[0][0])
                bot.send_photo(chat_id=channel_name, photo=photo)
            else:
                pass
            bot.send_message(chat_id=channel_name, text=answer_text[0])
            return sh.States.MENU
        else:
            logger.info("2 шаг согласования - else")
            keyboard = [['Модератор', 'Сотрудник']]

            reply_markup = ReplyKeyboardMarkup(keyboard,
                                               one_time_keyboard=True,
                                               resize_keyboard=True)

            user = update.message.from_user
            logger.info("Меню модератора вызвано пользователем {}.".format(user.id))
            bot.send_message(chat_id=user.id, text=press_mod['RU'], reply_markup=reply_markup)
            return sh.States.WHERE
    else:
        bot.send_message(chat_id=user.id, text=answer_neg['RU'])
        return sh.States.MENU


def answer_where(bot, update):
    user = update.message.from_user
    logger.info("Руководитель {} выбирает, кому отправить комментарии.".format(user.id))
    sh.set_state(sh.db_name, user.id, sh.States.WHERE.value)
    if update.message.text == 'Модератор':
        bot.send_message(chat_id=user.id, text=write_mod['RU'])
        return sh.States.ANSWER_MOD
    else:
        bot.send_message(chat_id=user.id, text=write_us['RU'])
        return sh.States.ANSWER_USER


def answer_mod(bot, update):
    user = update.message.from_user
    logger.info("Руководитель {} отправил комментарии модератору.".format(user.id))
    sh.set_state(sh.db_name, user.id, sh.States.ANSWER_MOD.value)
    post_time = calendar.timegm(time.gmtime())
    auth = db.SQLighter('db.sqlite')
    number_answers = len(auth.check_news(boss_id=user.id))
    answer_text = auth.check_news(user.id)[-1 * number_answers]
    checked_user = auth.select_cond('user_id', 'news_base', 'news_text', answer_text[0])[0][0]
    auth.update_cond('news_base', 'answer', answer_text[0], 'news_text', answer_text[0])
    auth.update_cond('news_base', 'answer_time', post_time, 'news_text', answer_text[0])
    auth.update_cond('news_base', 'status', 1, 'news_text', answer_text[0])
    bot.send_message(chat_id=user.id, text=answer_sent_mods['RU'])
    bot.send_message(chat_id=user.id, text='Непроверенных новостей: {}'
                     .format(len(auth.check_news(boss_id=user.id))))
    bot.send_message(chat_id=user.id, text=back2menu['RU'])
    bot.send_message(chat_id=checked_user, text=answer_sent_mods['RU'])
    if auth.select_cond('file_id', 'news_base', 'news_text', answer_text[0])[0][0]:
        photo = str(auth.select_cond('file_id', 'news_base', 'news_text', answer_text[0])[0][0])
        bot.send_photo(chat_id=channel_name, photo=photo)
    else:
        pass
    auth.update_cond('news_base', 'news_text', update.message.text, 'news_text', answer_text[0])
    bot.send_message(chat_id=channel_name, text=update.message.text)
    return sh.States.MENU


def answer_user(bot, update):
    user = update.message.from_user
    logger.info("Руководитель {} отправил комментарии сотруднику.".format(user.id))
    sh.set_state(sh.db_name, user.id, sh.States.ANSWER_USER.value)
    post_time = calendar.timegm(time.gmtime())
    auth = db.SQLighter('db.sqlite')
    number_answers = len(auth.check_news(boss_id=user.id))
    answer_text = auth.check_news(user.id)[-1 * number_answers]
    checked_user = auth.select_cond('user_id', 'news_base', 'news_text', answer_text[0])[0][0]
    auth.update_cond('news_base', 'answer', update.message.text, 'news_text', answer_text[0])
    auth.update_cond('news_base', 'answer_time', post_time, 'news_text', answer_text[0])
    bot.send_message(chat_id=checked_user, text=answer_acq_user['RU'])
    bot.send_message(chat_id=checked_user, text=update.message.text)
    bot.send_message(chat_id=user.id, text=answer_sent_user['RU'])
    bot.send_message(chat_id=user.id, text='Непроверенных новостей: {}'
                     .format(len(auth.check_news(boss_id=user.id))))
    bot.send_message(chat_id=user.id, text=back2menu['RU'])
    return sh.States.MENU


# general functions
FLAG = True


def callback(bot):
    while FLAG:
        time.sleep(60*60*24)
        auth = db.SQLighter('db.sqlite')
        current_time = calendar.timegm(time.gmtime())
        user = auth.select_no_cond('user_id', 'news_base')
        user_f = [user for user in user if len(str(user[0])) > 5]
        user_list = list(set([user[0] for user in user_f]))
        if user_list:
            rem_check = [user for user in user_list
                         if auth.select_cond('time', 'news_base', 'user_id', user)[-1][0] is not None
                         and
                         (current_time - auth.select_cond('time', 'news_base', 'user_id', user)[-1][0]) > (60*60*24*7)]
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
        # split time.sleep(60*60*12)
    pass


def cancel(bot, update):
    user = update.message.from_user
    logger.info("Пользователь {} прервал диалог.".format(user.id))
    update.message.reply_text(text=cancel_text['RU'], reply_markup=ReplyKeyboardRemove())
    sh.set_state(sh.db_name, user.id, sh.States.START.value)
    return ConversationHandler.END


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def restart_updater(bot):
    auth = db.SQLighter('db.sqlite')
    user = auth.select_no_cond('user_id', 'news_base')
    user_f = [user for user in user if len(str(user[0])) > 5]
    user_list = list(set([user[0] for user in user_f]))
    if user_list:
        for i in range(len(user_list)):
            bot.send_message(chat_id=user_list[i], text=repeater_update['RU'])
    else:
        pass


def start_collector(bot):
    a = request.Request().retrieve(url='https://api.telegram.org/bot{}/getUpdates'.format(config.token)).decode("utf-8")
    data = json.loads(str(a))
    if len(data['result']) > 0:
        for i in range(len(data['result'])):
            auth = db.SQLighter('db.sqlite')
            unique_id = int(data['result'][i]['message']['message_id'])
            cur_time = int(data['result'][i]['message']['date'])
            user_id = int(data['result'][i]['message']['from']['id'])
            bot.send_message(chat_id=user_id, text=sent_repeat['RU'])
            try:
                news_text = str(data['result'][i]['message']['text'])
                bot.send_message(chat_id=user_id, text=news_text)
                auth.insert_lost_news(unique_id, cur_time, user_id, news_text=news_text, file_id=None)
            except KeyError:
                try:
                    photo = str(data['result'][i]['message']['photo'][-1]['file_id'])
                    bot.send_photo(chat_id=user_id, photo=photo)
                    auth.insert_lost_news(unique_id, cur_time, user_id, news_text=None, file_id=photo)
                except KeyError:
                    try:
                        auth.insert_lost_news(unique_id, cur_time, user_id, news_text=None, file_id=None)
                    except KeyError:
                        pass
    else:
        pass


def main():
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            sh.States.MENU: [CommandHandler('menu', menu)],

            sh.States.SET_STATE: [RegexHandler(
                        '^({}|{}|{}|{})$'.format(
                            login_menu['RU'], news_menu['RU'], answer_menu['RU'], attach_menu['RU']), set_state)],

            sh.States.CHECK: [MessageHandler(Filters.text, check), CommandHandler('menu', menu)],

            sh.States.ATTACH: [MessageHandler(Filters.photo, send_photo), CommandHandler('send_news', send_news)],

            sh.States.NO_ATTACH: [MessageHandler(Filters.text, no_attachment), CommandHandler('send_news', send_news)],

            sh.States.SENT: [MessageHandler(Filters.text, send_news), CommandHandler('menu', menu)],

            sh.States.RESULT: [MessageHandler(Filters.text, answer_result)],

            sh.States.WHERE: [MessageHandler(Filters.text, answer_where)],

            sh.States.ANSWER_MOD: [MessageHandler(Filters.text, answer_mod)],

            sh.States.ANSWER_USER: [MessageHandler(Filters.text, answer_user)]
        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conversation_handler)

    # Log all errors:
    dp.add_error_handler(error)


if __name__ == '__main__':
    bot = updater.bot
    restart_updater(bot)
    start_collector(bot)
    main()
    p = Process(target=callback, args=(bot, ))
    p.start()
    updater.start_polling(clean=False)
