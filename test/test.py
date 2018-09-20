# import src.dbhelper as db_hp

data = {'ok': True, 'result': [{'update_id': 472405061, 'message': {'message_id': 5469, 'from': {'id': 125500294,
        'is_bot': False, 'first_name': 'Александр', 'username': 'alextimakov', 'language_code': 'ru-RU'},
        'chat': {'id': 125500294, 'first_name': 'Александр', 'username': 'alextimakov', 'type': 'private'},
        'date': 1537456498, 'text': 'timakov'}},
                               {'update_id': 472405062, 'message': {'message_id': 5470, 'from': {'id': 125500294,
        'is_bot': False, 'first_name': 'Александр', 'username': 'alextimakov', 'language_code': 'ru-RU'},
        'chat': {'id': 125500294, 'first_name': 'Александр', 'username': 'alextimakov', 'type': 'private'},
        'date': 1537456608, 'text': 'timakov'}}]}


def main():
    print(len(data['result'][0]['message']['from']['id']))


if __name__ == '__main__':
    main()