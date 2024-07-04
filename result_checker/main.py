import asyncio
import os
from time import sleep

import requests
import ydb
from dotenv import load_dotenv


def cloud_handler(event, context):
    return asyncio.run(cloud_run(event, context))


async def cloud_run(event, context):
    load_dotenv()

    driver_config = ydb.DriverConfig(endpoint=os.getenv('YDB_ENDPOINT'), database=os.getenv('YDB_DATABASE'),
                                     credentials=ydb.iam.MetadataUrlCredentials())

    driver = ydb.Driver(driver_config)

    try:
        driver.wait(timeout=5)
    except:
        return

    session = driver.table_client.session().create()

    db_requests = session.transaction().execute('SELECT * FROM requests WHERE stage == "P"',
                                                commit_tx=True)

    analysis_requests = db_requests[0].rows

    if analysis_requests is None or len(analysis_requests) == 0:
        return {
            'statusCode': 200,
            'body': 'Success'
        }

    for i, row in enumerate(analysis_requests):
        for k, v in row.items():
            if isinstance(v, (bytes, bytearray)):
                analysis_requests[i][k] = v.decode('utf8')

    analysis_requests = sorted(analysis_requests[0:5], key=lambda el: el['created_at'])

    for request in analysis_requests:
        request_id = request['id']
        user_id = request['user_id']
        attempt = request.get("attempt") if request.get("attempt") else 0

        if attempt >= 5:
            session.transaction().execute(f'UPDATE requests SET stage = "F" WHERE id == "{request_id}"',
                                          commit_tx=True)
            continue

        url = os.getenv('API_URL') + 'result/'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + os.getenv('API_TOKEN')
        }

        data = {
            "file_id": request['operation_id'],
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            session.transaction().execute(
                f'UPDATE requests SET stage = "S", attempt = {attempt + 1} WHERE id == "{request_id}"',
                commit_tx=True)

            db_user = session.transaction().execute(f'SELECT * FROM users WHERE id == "{user_id}"',
                                                    commit_tx=True)

            users = db_user[0].rows

            if users is None or len(users) == 0:
                continue

            user = users[0]

            for k, v in user.items():
                if isinstance(v, (bytes, bytearray)):
                    user[k] = v.decode('utf8')

            url = ''
            result_url = ''

            requests.post(
                url=url,
                data={
                    'chat_id': user['chat_id'],
                    'text': f"Анализ файла {request['file_name']} завершён.",
                    'reply_markup': {
                        'inline_keyboard': [[
                            {
                                'text': 'Просмотреть',
                                'web_app': {
                                    'url': f"{result_url}?file_id=" + request['operation_id']
                                }
                            },
                        ]]
                    }
                }
            )
        else:
            session.transaction().execute(f'UPDATE requests SET attempt = {attempt + 1} WHERE id == "{request_id}"',
                                          commit_tx=True)

        sleep(1)

    return {
        'statusCode': 200,
        'body': 'Success'
    }
