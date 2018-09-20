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

**Сделать - Сентябрь\Октябрь**
1. Аутентификация через e-mail
2. Создать администраторские права
2. Возможность добавлять / менять пары user-boss (дял админов, через handler)
3. Кол-во комментариев к 1 новости - в идеале > 1
4. Поставить корректный multiprocessing / multithreading
5. Перевести на MongoDB \ другую баз с поддержкой параллельных запросов (в sqlite - ошибки при одновременном запросе)
6. Добавить английский язык
7. Сделать напоминания привязанными к рабочему дню (допусловие по выходным и ночью)
8. Оценить переход на библиотеку типа asyncio (возможность работы с Inline Keyboard и большая гибкость)
11. Продумать взаимодействие Руководитель - Модератор
16. Упаковать в Docker (дальнейший деплой на корпоративном сервере)
17. Возможность редактировать новость с прежним unique id (для сотрудника)
19. Залить код на корпоративный github (1 стабильный билд)
20. Создать документацию и закинуть в Confluence
16. Выводить информацию о номере новости сотрудникам
20. Сделать graceful shutdown
23. Исправить Timed Out ошибку, возникающую после суток работы напоминалки
  
<del>Совместная отправка фото+текст (вложенный)</del>

<del>Новость с приложением - фото прикрепляется к новости и отправляется руководителю<del>

<del>Оповещение сотрудников о не-\успешных согласованиях</del> 

<del>Временная отправка на 1 юзера (вместо канала модераторов)</del>

<del>Оповещения - 1 раз в неделю, шаг - 24 часа, должны работать!</del>

<del>Добавить логин отправителя новости </del>

<del>Бот не присылает руководителю сразу новость, а только оповещение о ней</del>

<del>Возможность редактировать новость и согласовывать изменённую (для руководителей)</del>

<del>Встроить клавиши для более нативной навигации</del>

<del>Согласование - автоматически при получении новости</del>

<del>Счётчик новостей для каждого из руководителей</del>

<del>Вынести информацию о состоянии диалога во внешнее хранилище</del>

<del>Информацию после приёма сообщений надо сохранять в какую-либо внешнюю очередь</del>

