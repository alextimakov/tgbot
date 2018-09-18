import src.dbhelper as db_hp


def main():
    auth = db_hp.SQLighter('db.sqlite')
    user_id = 166823811
    user_uid = auth.select_user_id(user_id)  # выбираем пользователей, у которых есть несогласованные новости
    number_answers = auth.count_news(boss_id=user_id, status=0)  # чтобы начать проверять с самой ранней новости
    if user_uid:  # для контроля, является ли пользователь руководителем и есть ли несогласованные новости
        if number_answers > 0:  # доп проверка по кол-ву новостей
            answer_text = auth.check_news(user_id)[-1 * number_answers]
            if answer_text:
                print(str(auth.fetch_file_id(text=answer_text[0])[0]))
            else:
                print(2)


if __name__ == '__main__':
    main()

