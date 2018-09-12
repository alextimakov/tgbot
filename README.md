**News-Bot**
 
Код Telegram-бота для приёма сообщений от сотрудников компании и пересылки их соответствующим руководителям и модераторам

**Текущий функционал:**

1. Приветствие пользователя
2. Проверка пользователя в базе (по telegram id)
3. Проверка авторизации по базе
4. Возможность написать новость без приложения (только для сотрудников)
5. Возможность написать новость с приложением (только для сотрудников)
6. Возможность согласования новостей (только для руководителей)
7. Отправка новостей в канал модераторов в случае согласования
8. Отправка комментария обратно пользователю в случае доработок
9. Напоминание про необходимость написать новость (в случае превышения срока)

Бот временно тестируется на локале

**Сделать:**
1. Аутентификация через e-mail
2. Возможность добавлять / менять пары user-boss (handler)
3. Кол-во комментариев к 1 новости - сделать неограниченным
4. Поставить корректный мультипроцессинг (с обменом данными между состояниями)
5. Перевести на MongoDB
6. Добавить английский язык
7. Сделать напоминания привязанными к рабочему дню (не слать по выходным и ночью)
8. Перейти на библиотеку типа asyncio (возможность работы с Inline Keyboard и большая гибкость)
9. Согласование - автоматически при получении новости
10. Новость с приложением - фото прикрепляется к новости и отправляется модератору
11. Продумать взаимодействие Руководитель - Модератор
12. Совместная отправка фото+текст (вложенный)
13. Временная отправка на 1 юзера
14. Возможность редактировать новость и согласовывать изменённую (для руководителей)
15. Оповещения - 1 раз в неделю, шаг - 24 часа
16. Деплой на Docker + Cubernetes
17. Возможность редактировать новость с прежним unique id (для сотрудника)
18. Добавить логин отправителя новости 