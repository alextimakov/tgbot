def answer(bot, update):
    reply_keyboard = [['Согласовано', 'Не согласовано']]
    update.message.reply_text(
        'Ответ исполнителю:',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    bot.send_message(chat_id=channel_name, text=update.message.text)
    return


def answer_result(bot, update):
    # reply to sender of news
    user = update.message.from_user
    query = update.callback_query
    bot.send_message(chat_id=channel_name, text=query.message.text)
    logger.info("Ответ руководителя %s: %s", user.first_name, update.message.text)
    update.message.reply_text('Ваш ответ принят!', reply_markup=ReplyKeyboardRemove())
    return MENU


def reply_to_user(bot, update):
    last = db.setup('db2.csv')
    user = update.message.from_user
    reply_res = update.message.reply_to_message
    if not last.loc[last['message_id'] == reply_res.message_id]['status']:
        user_uid = db.get_user_id(user.id, user_base)
        bot.send_message(chat_id=user_uid, text=update.message.text)
