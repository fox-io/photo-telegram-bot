import json
import requests
import sched
import time
import shutil

# Initialize the global variable db.
db = {
    'data': {
        'files': [],
        'used_ids': [],
        'forward_list': [],
        'update_list': [],
    },
    'config': {
        'admins': [],
        'credentials': {
            'access_token': "",
            'channel': 0,
            'bot_id': 0
        },
        'delay': 60,
        'timezone': -5
    },
    'report': "",
    'need_report': False
}

# Initialize the scheduler.
scheduler = sched.scheduler(time.time, time.sleep)


def update():
    print('Updating\n--------')
    # Pull in the db.
    global db

    # Clear the report.
    print('- Clearing report.')
    db['report'] = ""

    # Load the config values from config.json.
    print('- Loading config...')
    with open('config.json') as config:
        # Load the config data from the file into a variable.
        configdata = json.load(config)

        # Save the credentials to the db.
        db['config']['credentials']['access_token'] = configdata['credentials']['telegramAccessToken']
        print('  - Telegram access token loaded.')

        db['config']['credentials']['channel'] = configdata['credentials']['telegramChannel']
        print('  - Telegram channel loaded.')

        db['config']['credentials']['bot_id'] = configdata['credentials']['telegramBotID']
        print('  - Telegram bot ID loaded.')

        # Save the admins list to the db.
        db['config']['admins'] = configdata['admins']
        print('  - Loaded ' + str(len(db['config']['admins'])) + ' admins.')

        # Save the post delay to the db.
        db['config']['delay'] = configdata['delay']
        print('  - Loaded ' + str(db['config']['delay']) + ' minute delay.')

        # Save the timezone to the db.
        db['config']['timezone'] = configdata['timezone']
        print('  - Loaded timezone UTC ' + str(db['config']['timezone']))

    # Load the data values from data.json.
    print('- Loading data...')
    with open('data.json') as data:
        # Load the data from the file into a variable.
        data = json.load(data)

        # Save the files list to the db.
        db['data']['files'] = data['files']
        print('  - Loaded ' + str(len(db['data']['files'])) + ' files.')

        # Save the used IDs list to the db.
        db['data']['used_ids'] = data['usedIDs']
        print('  - Loaded ' + str(len(db['data']['used_ids'])) + ' used IDs.')

        # Save the forward list to the db.
        db['data']['forwardList'] = data['forwardList']
        print('  - Loaded ' + str(len(db['data']['forwardList'])) + ' forwards.')

    # Get the latest updates from the Telegram bot.
    print('- Getting updates')
    request = 'https://api.telegram.org/bot' + db['config']['credentials']['access_token'] + '/getUpdates'
    response = requests.get(request)
    response = response.json()
    if response['ok']:
        print('  - Response OK.')
        db['data']['update_list'] = response['result']
    else:
        print('  - Response not OK.')
    # BREAK

    # Print the number of updates received.
    print('  - Updates:', len(db['data']['update_list']))

    while len(db['data']['update_list']) > 0:
        for i in range(len(db['data']['update_list'])):
            # Dumps the list of updates to the console.
            # print('update_id:', db['data']['update_list'][i]['update_id'], '|', end=' ')

            if 'message' in db['data']['update_list'][i]:
                if db['data']['update_list'][i]['message']['chat']['id'] in db['config']['admins']:
                    if 'document' in db['data']['update_list'][i]['message']:
                        # Save the caption to the document json object
                        if 'caption' in db['data']['update_list'][i]['message']:
                            db['data']['update_list'][i]['message']['document']['caption'] = db['data']['update_list'][i]['message']['caption']

                        # Dump the update information to console.
                        # print(json.dumps(db['data']['update_list'][i]['message']['document'], indent=2, sort_keys=True))

                        if db['data']['update_list'][i]['message']['document'] in db['data']['files']:
                            print('Skipping previously added file.')
                        else:
                            db['data']['files'].append(db['data']['update_list'][i]['message']['document'])
                            print('file added', end=' ')
                            if 'from' in db['data']['update_list'][i]['message']:
                                if 'username' in db['data']['update_list'][i]['message']['from']:
                                    print('(from ', db['data']['update_list'][i]['message']['from']['username'], ')', sep='')
                                else:
                                    print('(from ', db['data']['update_list'][i]['message']['from']['first_name'], ' (',
                                          db['data']['update_list'][i]['message']['from']['id'], '))', sep='')
                            else:
                                print()
                    else:
                        # MESSAGE DOESN'T CONTAIN A FILE, PUT PARSE CODE HERE
                        print('message does not contain a file', end=' ')
                        if 'from' in db['data']['update_list'][i]['message']:
                            if 'username' in db['data']['update_list'][i]['message']['from']:
                                print('(from ', db['data']['update_list'][i]['message']['from']['username'], ')', sep='')
                            else:
                                print('(from ', db['data']['update_list'][i]['message']['from']['first_name'], ' (',
                                      db['data']['update_list'][i]['message']['from']['id'], '))', sep='')
                        else:
                            print()
                else:
                    print('update not from admin', end=' ')
                    if 'new_chat_member' in db['data']['update_list'][i]['message']:
                        if db['data']['update_list'][i]['message']['new_chat_member']['id'] == db['config']['credentials']['bot_id']:
                            db['data']['forward_list'].append(db['data']['update_list'][i]['message']['chat']['id'])
                            if 'username' in db['data']['update_list'][i]['message']['from']:
                                print('\nadded ', db['data']['update_list'][i]['message']['chat']['title'], ' (',
                                      db['data']['update_list'][i]['message']['chat']['id'], ') to forwardList by ',
                                      str(db['data']['update_list'][i]['message']['from']['username']), ' (',
                                      db['data']['update_list'][i]['message']['from']['id'], ')', sep='')
                                db['report'] = db['report'] + '`added `' + str(
                                    db['data']['update_list'][i]['message']['chat']['title']) + '` to forwardList by `%40' + str(
                                    db['data']['update_list'][i]['message']['from']['username']) + '\n'  # %40 = @
                            else:
                                print('\nadded ', db['data']['update_list'][i]['message']['chat']['title'], ' (',
                                      db['data']['update_list'][i]['message']['chat']['id'], ') to forwardList by ',
                                      str(db['data']['update_list'][i]['message']['from']), sep='')
                                db['report'] = db['report'] + '`added `' + str(
                                    db['data']['update_list'][i]['message']['chat']['title']) + '` to forwardList by `' + str(
                                    db['data']['update_list'][i]['message']['from']['first_name']) + ' (' + str(
                                    db['data']['update_list'][i]['message']['from']['id']) + ')\n'
                            db['need_report'] = True
                    elif 'left_chat_member' in db['data']['update_list'][i]['message']:
                        if db['data']['update_list'][i]['message']['left_chat_member']['id'] == db['config']['credentials']['bot_id']:
                            if db['data']['update_list'][i]['message']['chat']['id'] in db['data']['forward_list']:
                                db['data']['forward_list'].remove(db['data']['update_list'][i]['message']['chat']['id'])
                                print('\nremoved', db['data']['update_list'][i]['message']['chat']['title'], 'from forwardList')
                                db['report'] = db['report'] + '`removed `' + str(
                                    db['data']['update_list'][i]['message']['chat']['title']) + ' `from forwardList`\n'
                                db['need_report'] = True
                    else:
                        if 'from' in db['data']['update_list'][i]['message']:
                            if 'username' in db['data']['update_list'][i]['message']['from']:
                                print('(from ', db['data']['update_list'][i]['message']['from']['username'], ')', sep='')
                            else:
                                print('(from ', db['data']['update_list'][i]['message']['from']['first_name'], ' (',
                                      db['data']['update_list'][i]['message']['from']['id'], '))', sep='')
                        else:
                            print()
                        print('   ', db['data']['update_list'][i]['message'])
            else:
                print('update not does not contain message')
                print(db['data']['update_list'][i])
        if len(db['data']['update_list']) > 0:
            mostrecentupdate = db['data']['update_list'][len(db['data']['update_list']) - 1]['update_id']
            print('clearing update_list through to update_id', mostrecentupdate + 1)
            request = 'https://api.telegram.org/bot' + db['config']['credentials']['access_token'] + '/getUpdates'
            response = requests.get(request + '?offset=' + str(mostrecentupdate + 1))
            response = response.json()
            if response['ok']:
                db['data']['update_list'] = response['result']
                print(' updates:', len(db['data']['update_list']))
                if len(db['data']['update_list']) <= 0:
                    print('...success')
                else:
                    print('update_list not empty, repeating...')
            else:
                print('failed')
                db['need_report'] = True
    else:
        print('update_list empty')

    print()


def report_forwards():
    print()
    global db
    db['report'] = ''

    with open('data.json') as data:
        data = json.load(data)
        db['data']['forward_list'] = data['forwardList']
        print(len(db['data']['forward_list']), 'forwards')
    print()

    request = 'https://api.telegram.org/bot' + db['config']['credentials']['access_token'] + '/getChat'

    for i in range(len(db['data']['forward_list'])):
        response = requests.get(request + '?chat_id=' + str(db['data']['forward_list'][i]))
        response = response.json()
        if response['ok']:
            print('forward[', str(i), ']: (', str(response['result']['id']), ') ', response['result']['title'], sep='')
            db['report'] = db['report'] + '`forward[' + str(i) + ']: `' + response['result']['title'] + '\n'
        else:
            print('forward[', str(i), ']: (', str(db['data']['forward_list'][i]), ') ', response['description'], sep='')

    print()


def update_data_file():
    # Saves all the data to the data.json file.
    global db

    with open('data.json', 'w') as data:
        json.dump({
            'files': db['data']['files'],
            'usedIDs': db['data']['used_ids'],
            'forwardList': db['data']['forward_list'],
        }, data)

    print('data.json updated')


def post_photo():
    print()
    global db
    remove_list = []
    is_image = True
    forward_message = True

    if len(db['data']['files']) > 0:
        file_to_send = db['data']['files'][0]
        filename = 'image'
        filecaption = ''
        link = None
        request = 'https://api.telegram.org/bot' + db['config']['credentials']['access_token'] + '/getFile?file_id=' + file_to_send['file_id']
        # print(request)
        response = requests.get(request)
        response = response.json()
        if response['ok']:
            if 'image' in file_to_send['mime_type']:
                filename = filename + '.' + file_to_send['mime_type'][6:]  # cuts off the first 6 characters ('image/')
                try:
                    filecaption = file_to_send['caption']
                except KeyError:
                    filecaption = ''

            else:
                is_image = False
                mime_type = file_to_send['mime_type'].split('/')
                filename = filename + '.' + mime_type[1]  # uses anything found after the slash
            print('downloading...', end='')
            request = 'https://api.telegram.org/file/bot' + db['config']['credentials']['access_token'] + '/' + response['result']['file_path']
            response = requests.get(request, stream=True)  # stream=True IS REQUIRED
            print('done.', end='')
            if response.status_code == 200:
                with open(filename, 'wb') as image:
                    shutil.copyfileobj(response.raw, image)
            print(' saved as ' + filename)
        else:
            print('response not ok')
            db['report'] = db['report'] + '`post failed.`\n`photo re-added to queue.`'
            return  # we don't have a sendable file, so just return

        image_file = open(filename, 'rb')

        # send to telegram
        if is_image:
            print('sending photo to telegram, chat_id:' + str(db['config']['credentials']['channel']) + '...', end='')
            request = 'https://api.telegram.org/bot' + db['config']['credentials']['access_token'] + '/sendPhoto'
            telegramfile = {'photo': image_file}
            if filecaption is not None:
                sent_file = requests.get(
                    request + '?chat_id=' + str(db['config']['credentials']['channel']) + '&caption=' + filecaption.replace('&', '%26'),
                    files=telegramfile)
            else:
                sent_file = requests.get(request + '?chat_id=' + str(db['config']['credentials']['channel']), files=telegramfile)
            if sent_file.json()['ok']:
                sent_file = sent_file.json()
                if len(db['data']['files']) <= 10:
                    db['report'] = db['report'] + '`telegram...success.`'
                    db['need_report'] = True
                else:
                    db['report'] = db['report'] + '`telegram...success.`'
                db['data']['used_ids'].append(sent_file['result']['photo'][-1]['file_id'])
                db['data']['files'].pop(0)
                print('success.')
            else:
                print('sent_file not ok, skipping forwards')
                print(sent_file.json())
                db['report'] = db['report'] + '`post failed.`\n`photo re-added to queue.`'
                print('failed.')
                db['need_report'] = True
                forward_message = False
        else:
            print('sending file to telegram, chat_id:' + str(db['config']['credentials']['channel']) + '...', end='')
            if link is not None:
                request = 'https://api.telegram.org/bot' + db['config']['credentials']['access_token'] + '/sendDocument?chat_id=' + str(
                    db['config']['credentials']['channel']) + '&document=' + file_to_send['file_id'] + '&caption=' + link.replace('&', '%26')
            else:
                request = 'https://api.telegram.org/bot' + db['config']['credentials']['access_token'] + '/sendDocument?chat_id=' + str(
                    db['config']['credentials']['channel']) + '&document=' + file_to_send['file_id']
            sent_file = requests.get(request)
            if sent_file.json()['ok']:
                sent_file = sent_file.json()
                if len(db['data']['files']) <= 10:
                    db['report'] = db['report'] + '`telegram...success.`'
                    db['need_report'] = True
                # else :
                # db['report'] = db['report'] + '`telegram...success.`'
                db['data']['files'].pop(0)
                print('success.')
            else:
                print('sent_file not ok, skipping forwards')
                print(sent_file.json())
                db['report'] = db['report'] + '`post failed.`\n`photo re-added to queue.`'
                print('failed.')
                db['need_report'] = True
                forward_message = False

        # FORWARDING PHOTO
        if forward_message:
            print('forwarding photo to', len(db['data']['forward_list']), 'chats...', end='')
            successful_forwards = 0
            for i in range(len(db['data']['forward_list'])):
                request = requests.get('https://api.telegram.org/bot' + db['config']['credentials']['access_token'] + '/forward_message?chat_id=' + str(
                    db['data']['forward_list'][i]) + '&from_chat_id=' + str(db['config']['credentials']['channel']) + '&message_id=' + str(
                    sent_file['result']['message_id']))
                response = request.json()
                if response['ok']:
                    successful_forwards = successful_forwards + 1
                # print('forward[' + str(i) + '] ok')
                elif 'description' in response:
                    if 'Forbidden' in response['description']:
                        remove_list.append(db['data']['forward_list'][i])
                        db['report'] = db['report'] + '\n` removed `' + str(db['data']['forward_list'][i]) + '` from forward list`'
                        db['need_report'] = True
                    elif ('group chat was upgraded to a supergroup chat' in response['description'] and
                          'parameters' in response and 'migrate_to_chat_id' in response['parameters']):
                        db['data']['forward_list'][i] = response['parameters']['migrate_to_chat_id']
                        # try again
                        print('\ntrying with new ID...', end='')
                        secondtry = requests.get(
                            'https://api.telegram.org/bot' + db['config']['credentials']['access_token'] + '/forward_message?chat_id=' + str(
                                db['data']['forward_list'][i]) + '&from_chat_id=' + str(db['config']['credentials']['channel']) + '&message_id=' + str(
                                sent_file['result']['message_id']))
                        if secondtry.json()['ok']:
                            successful_forwards = successful_forwards + 1
                            print('success.')
                        else:
                            db['need_report'] = True
                            print('failed')
                else:
                    getchat = requests.get(
                        'https://api.telegram.org/bot' + db['config']['credentials']['access_token'] + '/getChat?chat_id=' + str(db['data']['forward_list'][i]))
                    getchat = getchat.json()
                    if getchat['ok']:
                        print('\nforward[' + str(i) + '] failed (chat_id: ' + str(db['data']['forward_list'][i]) + ') ' +
                              getchat['result']['title'], end='')
                        db['report'] = db['report'] + '\n`forward[`' + str(i) + '`] failed (chat_id: `' + str(
                            db['data']['forward_list'][i]) + '`) ` ' + getchat['result']['title']
                        db['need_report'] = True
                    else:
                        if 'description' in getchat:
                            print('\nforward[' + str(i) + '] failed (chat_id: ' + str(db['data']['forward_list'][i]) + ') ' + getchat[
                                'description'], end='')
                            db['report'] = db['report'] + '\n`forward[`' + str(i) + '`] failed (chat_id: `' + str(
                                db['data']['forward_list'][i]) + '`) `' + getchat['description']
                            if 'Forbidden' in getchat['description']:
                                remove_list.append(db['data']['forward_list'][i])
                                db['report'] = db['report'] + '\n` removed `' + str(db['data']['forward_list'][i]) + '` from forward list`'
                                db['need_report'] = True
                        else:
                            print('\nforward[' + str(i) + '] failed (chat_id: ' + str(db['data']['forward_list'][i]) + ')', end='')
                            db['report'] = db['report'] + '\n`forward[`' + str(i) + '`] failed (chat_id: `' + str(
                                db['data']['forward_list'][i]) + '`)'
                            db['need_report'] = True
                    if 'description' in response:
                        db['report'] = db['report'] + ' reason: `' + response['description']
                    else:
                        db['report'] = db['report'] + '`'
                    print('\nraw response:', response, end='')
                    print('\nraw command:', request.url)
            db['report'] = db['report'] + '\n` forwarded to: `' + str(successful_forwards) + '` chats`'
            print('done. ')
    else:
        db['report'] = db['report'] + '`post failed.`\n`no photos in queue.`\nADD PHOTOS IMMEDIATELY'
        db['need_report'] = True
    if len(remove_list) > 0:
        for i in range(len(remove_list)):
            db['data']['forward_list'].remove(remove_list[i])


def schedule_nextupdate():
    print()
    # reinitialize all the lists and variables as global
    global db
    global scheduler

    nextupdate = currenttime = (time.time() + ((60 * 60) * db['config']['timezone']))
    nextupdate = (nextupdate - (nextupdate % (db['config']['delay'] * 60))) + (db['config']['delay'] * 60)

    noowtime = ''
    if time.localtime(currenttime).tm_hour < 10:
        noowtime = noowtime + '0'
    noowtime = noowtime + str(time.localtime(currenttime).tm_hour) + ':'
    if time.localtime(currenttime).tm_min < 10:
        noowtime = noowtime + '0'
    noowtime = noowtime + str(time.localtime(currenttime).tm_min)

    nexttime = ''
    if time.localtime(nextupdate).tm_hour < 10:
        nexttime = nexttime + '0'
    nexttime = nexttime + str(time.localtime(nextupdate).tm_hour) + ':'
    if time.localtime(nextupdate).tm_min < 10:
        nexttime = nexttime + '0'
    nexttime = nexttime + str(time.localtime(nextupdate).tm_min)

    db['report'] = db['report'] + '\n`current delay: `' + str(db['config']['delay']) + '` minutes\ncurrent queue: `' + str(
        len(db['data']['files'])) + '`\n current time: `' + noowtime + '`\n  next update: `' + nexttime
    if len(db['data']['files']) < 10:
        db['report'] = db['report'] + '\nLOW ON PHOTOS'
        db['need_report'] = True
    # db['report'] = db['report'] + '\n`next photo in queue: `'

    print('current time:', noowtime)
    print(' next update:', nexttime)
    print()
    print('scheduling update for', db['config']['delay'], 'minutes from now')
    # scheduler.enter((db['config']['delay'] * 60), 1, scheduled_post, ())
    scheduler.enterabs((nextupdate - (3600 * db['config']['timezone'])), 1, scheduled_post, ())


def schedule_firstupdate():
    print()
    # reinitialize all the lists and variables as global
    global db
    global scheduler

    nextupdate = currenttime = (time.time() + ((60 * 60) * db['config']['timezone']))
    nextupdate = (nextupdate - (nextupdate % (db['config']['delay'] * 60))) + (db['config']['delay'] * 60)

    noowtime = ''
    if time.localtime(currenttime).tm_hour < 10:
        noowtime = noowtime + '0'
    noowtime = noowtime + str(time.localtime(currenttime).tm_hour) + ':'
    if time.localtime(currenttime).tm_min < 10:
        noowtime = noowtime + '0'
    noowtime = noowtime + str(time.localtime(currenttime).tm_min)

    nexttime = ''
    if time.localtime(nextupdate).tm_hour < 10:
        nexttime = nexttime + '0'
    nexttime = nexttime + str(time.localtime(nextupdate).tm_hour) + ':'
    if time.localtime(nextupdate).tm_min < 10:
        nexttime = nexttime + '0'
    nexttime = nexttime + str(time.localtime(nextupdate).tm_min)

    db['report'] = db['report'] + '`  bot started`\n`current delay: `' + str(db['config']['delay']) + '` minutes`\n`current queue: `' + str(
        len(db['data']['files'])) + '\n`     forwards: `' + str(
        len(db['data']['forward_list'])) + '\n` current time: `' + noowtime + '\n`  next update: `' + nexttime
    # db['report'] = db['report'] + '\n`next photo in queue: `'

    print('current time:', noowtime)
    print('next update: ', nexttime)
    print('bot started. scheduling first post...')
    print('scheduling update for', nexttime)
    # post_photo()
    scheduler.enterabs((nextupdate - (3600 * db['config']['timezone'])), 1, scheduled_post, ())


# https://stackoverflow.com/a/1267145/8197207
def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def send_report():
    print()
    # reinitialize all the lists and variables as global
    global db

    if len(db['data']['files']) > 0:
        request = 'https://api.telegram.org/bot' + db['config']['credentials']['access_token'] + '/sendMessage'
        for i in range(len(db['config']['admins'])):
            request = requests.get(request + '?chat_id=' + str(db['config']['admins'][i]) + '&text=' + db['report'] + '&parse_mode=Markdown')
            response = request.json()
            if response['ok']:
                print('db[\'report\'][' + str(i) + ']: ok')
            else:
                print('db[\'report\'][' + str(i) + ']: failed (' + str(db['config']['admins'][i]) + ')')
                if 'description' in response:
                    print('reason: ' + response['description'])
                print('raw response:', response)
                print('raw request:', request.url)
    else:
        request = 'https://api.telegram.org/bot' + db['config']['credentials']['access_token'] + '/sendMessage'
        for i in range(len(db['config']['admins'])):
            requests.get(request + '?chat_id=' + str(db['config']['admins'][i]) + '&text=' + db['report'] + '&parse_mode=Markdown')
            requests.get(request + '?chat_id=' + str(db['config']['admins'][i]) + '&text=NO PHOTOS IN QUEUE&parse_mode=Markdown')

    print('report sent')


def initial_startup():
    print('initial_startup()')
    # reinitialize all the lists and variables as global
    global scheduler

    report_forwards()
    update()
    update_data_file()
    schedule_firstupdate()
    send_report()

    scheduler.run()


def scheduled_post():
    print()
    global scheduler
    global db

    update()
    post_photo()
    update_data_file()
    schedule_nextupdate()
    if db['need_report']:
        send_report()
    db['need_report'] = False
    scheduler.run()


initial_startup()
