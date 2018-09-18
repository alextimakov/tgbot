import src.dbhelper as db_hp


def main():
    auth = db_hp.SQLighter('db.sqlite')
    user_uid = auth.select_user_id(203411538)  # выбираем пользователей, у которых есть несогласованные новости
    number_answers = auth.count_news(boss_id=203411538, status=0)  # чтобы начать проверять с самой ранней новости
    answer_text = auth.check_news(203411538)[-1 * number_answers]
    checked_user = auth.select_id_by_news(text=answer_text[0])[0]
    comment = auth.select_user_by_id(id=checked_user)[0]
    print(comment)


if __name__ == '__main__':
    main()

