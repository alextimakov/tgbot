from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler)
from telegram.utils import request
import time
import calendar
import logging
import json
from multiprocessing import Process
import src.dbhelper as db_hp
import src.config as config
from src.scripts import *
import src.shelve as sh
# import socks

channel_name = '@findaride'

updater = Updater(token=config.token, request_kwargs=config.REQUEST_KWARGS)  # Токен API к Telegram
dp = updater.dispatcher

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Global vars:
unique_token = 0


def start(bot, update):
    user = update.message.from_user
    auth = db_hp.SQLighter('db.sqlite')
    all_ids = []
    for i in range(auth.count_rows()):
        all_ids.extend([auth.select_all()[i][2], auth.select_all()[i][3]])
    for i in range(len(all_ids)):
        if user.id in all_ids:
            bot.send_message(chat_id=update.message.chat_id, text=login_check_repeat['RU'])
            state = sh.get_current_state(sh.db_name, user.id)
            logger.info("Пользователь {} в состоянии {}".format(user.id, int(state)))
            if int(state) == int(sh.States.LOGIN.value):
                bot.send_message(chat_id=user.id, text='Бот был перезапущен, вы остановились на авторизации')
                login(bot, update)
                return sh.States.CHECK
            elif int(state) == int(sh.States.NEWS.value):
                bot.send_message(chat_id=user.id, text='Вы остановились на отправке фото.\n'
                                                       'Нажмите /cancel, если хотите начать с начала')
                news(bot, update)
                return sh.States.ATTACH
            elif int(state) == int(sh.States.NO_ATTACH.value):
                bot.send_message(chat_id=user.id,
                                 text='Вы остановились на написании новости.\n'
                                      'Нажмите /cancel, если хотите начать с начала')
                no_attachment(bot, update)
                return sh.States.SENT
            elif int(state) == int(sh.States.ANSWER.value):
                bot.send_message(chat_id=user.id,
                                 text='Вы остановились на согласовании новости.\n'
                                      'Нажмите /cancel, если хотите начать с начала')
                answer(bot, update)
                return sh.States.RESULT
            else:
                bot.send_message(chat_id=user.id, text=welcome_text['RU'])
                bot.send_message(chat_id=user.id, text=login_check_init_suc['RU'])
                return sh.States.MENU
        else:
            login(bot, update)
            return sh.States.CHECK


def menu(bot, update):
    keyboard = [[login_menu['RU'], news_menu['RU']],
                [answer_menu['RU'], attach_menu['RU']]]

    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard=True,
                                       resize_keyboard=True)

    user = update.message.from_user
    logger.info("Меню вызвано пользователем {}.".format(user.first_name))
    sh.set_state(sh.db_name, user.id, sh.States.MENU.value)
    update.message.reply_text(menu_text['RU'], reply_markup=reply_markup)
    return sh.States.SET_STATE


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


# login procedure
def login(bot, update):
    user = update.message.from_user
    logger.info("{} пытается авторизоваться.".format(user.first_name))
    sh.set_state(sh.db_name, user.id, sh.States.LOGIN.value)
    update.message.reply_text(login_req['RU'])
    return sh.States.CHECK


def check(bot, update):
    user = update.message.from_user
    logger.info("{} отправил логин.".format(user.first_name))
    sh.set_state(sh.db_name, user.id, sh.States.CHECK.value)
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
        return sh.States.MENU
    else:
        bot.send_message(chat_id=update.message.chat_id, text=login_check_fail['RU'])
        bot.send_message(chat_id=update.message.chat_id, text=back2menu['RU'])
        return sh.States.CHECK


# news procedure
def news(bot, update):
    user = update.message.from_user
    logger.info("%s начал писать новость с приложением", user.first_name)
    sh.set_state(sh.db_name, user.id, sh.States.NEWS.value)
    update.message.reply_text(attach_req['RU'])
    auth = db_hp.SQLighter('db.sqlite')
    if auth.select_boss_id(user.id):  # проверяем, есть ли в базе руководитель юзера
        boss_uid = auth.select_boss_id(user.id)
        if auth.select_user_id(boss_uid):  # проверяем, есть ли в базе сам юзер
            global unique_token
            unique_token = update.message.message_id
            auth.insert_news_start(id=unique_token, status=0, user_id=user.id, boss_id=boss_uid[0])
        else:
            bot.send_message(chat_id=update.message.chat_id, text=user_not_found['RU'])
    else:
        bot.send_message(chat_id=update.message.chat_id, text=boss_not_found['RU'])
    return sh.States.ATTACH


# news with attachment
def send_photo(bot, update):
    user = update.message.from_user
    auth = db_hp.SQLighter('db.sqlite')
    logger.info("%s отправил фотографию", user.first_name)
    sh.set_state(sh.db_name, user.id, sh.States.ATTACH.value)
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
        return sh.States.MENU
    else:
        update.message.reply_text(news_req['RU'])
        return sh.States.SENT


# news without attachment
def no_attachment(bot, update):
    user = update.message.from_user
    logger.info("{} начал писать новость без приложения.".format(user.first_name))
    sh.set_state(sh.db_name, user.id, sh.States.NO_ATTACH.value)
    bot.send_message(chat_id=update.message.chat_id, text=news_req['RU'])
    auth = db_hp.SQLighter('db.sqlite')
    boss_uid = auth.select_boss_id(user.id)
    if auth.select_boss_id(user.id):  # проверяем, есть ли в базе руководитель юзера
        boss_uid = auth.select_boss_id(user.id)
        if auth.select_user_id(boss_uid):  # проверяем, есть ли в базе сам юзер
            global unique_token
            unique_token = update.message.message_id
            auth.insert_news_start(id=unique_token, status=0, user_id=user.id, boss_id=boss_uid[0])
        else:
            bot.send_message(chat_id=update.message.chat_id, text=user_not_found['RU'])
    else:
        bot.send_message(chat_id=update.message.chat_id, text=boss_not_found['RU'])
    return sh.States.SENT


def send_news(bot, update):
    user = update.message.from_user
    auth = db_hp.SQLighter('db.sqlite')
    boss_uid = auth.select_boss_id(user.id)[0]
    bot.send_message(chat_id=boss_uid, text=new_news['RU'])
    logger.info("%s отправил текст новости", user.first_name)
    sh.set_state(sh.db_name, user.id, sh.States.SENT.value)
    post_time = calendar.timegm(time.gmtime())
    auth.update_news_text(time=post_time, text=update.message.text, key=unique_token)
    update.message.reply_text(news_acq['RU'])
    bot.send_message(update.message.chat.id, 'Новость успешно отправлена руководителю!')
    update.message.reply_text(back2menu['RU'])
    return sh.States.MENU


# answer procedure
def answer(bot, update):
    user = update.message.from_user
    logger.info("Руководитель проверил обновления %s", user.first_name)  # руководитель заходит в согласование
    sh.set_state(sh.db_name, user.id, sh.States.ANSWER.value)
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
                return sh.States.RESULT
            else:
                bot.send_message(chat_id=user.id, text='Новость не содержит текста и приложений. Нажмите /cancel')
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
    post_time = calendar.timegm(time.gmtime())
    auth = db_hp.SQLighter('db.sqlite')
    number_answers = auth.count_news(boss_id=user.id, status=0)
    answer_text = auth.check_news(user.id)[-1 * number_answers]
    checked_user = auth.select_id_by_news(text=answer_text[0])[0]
    logger.info("Ответ руководителя %s: %s", user.first_name, update.message.text)
    sh.set_state(sh.db_name, user.id, sh.States.RESULT.value)
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
        return sh.States.MENU
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
        return sh.States.WHERE


def answer_where(bot, update):
    user = update.message.from_user
    logger.info("Руководитель {} выбирает, кому отправить комментарии.".format(user.first_name))
    sh.set_state(sh.db_name, user.id, sh.States.WHERE.value)
    if update.message.text == 'Модератор':
        bot.send_message(chat_id=user.id, text='Введите изменённый текст новости для отправки модератору')
        return sh.States.ANSWER_MOD
    else:
        bot.send_message(chat_id=user.id, text='Введите изменённый текст новости для отправки сотруднику')
        return sh.States.ANSWER_USER


def answer_mod(bot, update):
    user = update.message.from_user
    logger.info("Руководитель {} отправил комментарии модератору.".format(user.first_name))
    sh.set_state(sh.db_name, user.id, sh.States.ANSWER_MOD.value)
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
    return sh.States.MENU


def answer_user(bot, update):
    user = update.message.from_user
    logger.info("Руководитель {} отправил комментарии сотруднику.".format(user.first_name))
    sh.set_state(sh.db_name, user.id, sh.States.ANSWER_USER.value)
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
    return sh.States.MENU


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

    sh.set_state(sh.db_name, user.id, sh.States.START.value)
    return ConversationHandler.END


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)


def restart_updater(bot):
    auth = db_hp.SQLighter('db.sqlite')
    user = auth.fetch_user_id_news()
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
            auth = db_hp.SQLighter('db.sqlite')
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
    # Add conversation handler with predefined states:
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

    # dp.add_handler(initial_message)
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
