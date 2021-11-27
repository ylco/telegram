# encoding:utf-8

from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest
import sys
import csv
import traceback
import time
import random
import re

index = 0
api_hash = []
client = None
client_arr = []


# api_id = '' # YOUR API_ID
# api_hash = ''  # YOUR API_HASH
# phone = ''  # YOUR PHONE NUMBER, INCLUDING COUNTRY CODE


def init_tg_connect():
    global client
    if client_arr[index] is None:
        print("API ID 为空")
        return None
    client = client_arr[index]
    # client = TelegramClient(api_hash[index]['phone'], api_hash[index]['api_id'], api_hash[index]['api_hash'])
    # client.connect()
    # if not client.is_user_authorized():
    #     client.send_code_request(api_hash[index]['phone'])
    #     client.sign_in(api_hash[index]['phone'], input('Enter the code: '))


def read_api_hash_file():
    with open("./hash.csv", encoding='UTF-8') as f:
        rows = csv.reader(f, delimiter=",", lineterminator="\n")
        # next(rows, None)
        for row in rows:
            tgclient = TelegramClient(row[2], row[0], row[1])
            tgclient.connect()
            if not tgclient.is_user_authorized():
                tgclient.send_code_request(row[2])
                tgclient.sign_in(row[2], input('Enter the code: '))
            client_arr.append(tgclient)
            # has = {}
            # has['api_id'] = row[0]
            # has['api_hash'] = row[1]
            # has['phone'] = row[2]
            # api_hash.append(has)


def add_users_to_group():
    global index
    input_file = sys.argv[1]
    users = []
    with open(input_file, encoding='UTF-8') as f:
        rows = csv.reader(f, delimiter=",", lineterminator="\n")
        next(rows, None)
        for row in rows:
            user = {}
            user['username'] = row[0]
            try:
                user['id'] = int(row[1])
                user['access_hash'] = int(row[2])
            except IndexError:
                print('users without id or access_hash')
            users.append(user)

    # random.shuffle(users)
    chats = []
    last_date = None
    chunk_size = 10
    groups = []

    result = client(GetDialogsRequest(
        offset_date=last_date,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=chunk_size,
        hash=0
    ))
    chats.extend(result.chats)

    for chat in chats:
        try:
            if chat.megagroup == True:  # CONDITION TO ONLY LIST MEGA GROUPS.
                groups.append(chat)
        except:
            continue

    print('Choose a group to add members:')
    i = 0
    for group in groups:
        print(str(i) + '- ' + group.title)
        i += 1

    g_index = input("Enter a Number: ")
    target_group = groups[int(g_index)]
    print('\n\nGrupo elegido:\t' + groups[int(g_index)].title)

    target_group_entity = InputPeerChannel(target_group.id, target_group.access_hash)

    mode = int(input("输入 1 使用用户账号添加进Telegram 群组 输入 2 使用用户ID添加进入群组: "))

    error_count = 0
    n = 0
    for user in users:
        try:
            print("Adding {}".format(user['username']))
            if mode == 1:
                if user['username'] == "":
                    continue
                user_to_add = client.get_input_entity(user['username'])
            elif mode == 2:
                user_to_add = InputPeerUser(user['id'], user['access_hash'])
            else:
                sys.exit("Invalid Mode Selected. Please Try Again.")
            client(InviteToChannelRequest(target_group_entity, [user_to_add]))
            print("请等待60秒。。。正在运行中")
            del users[n]
            n += 1
            time.sleep(60)
        except PeerFloodError:
            print("从Telegram中获取错误信息 脚本已停止 请过一段时间再次重试")
            index += 1
            init_tg_connect()
        except UserPrivacyRestrictedError:
            print("您所添加的用户已设置为 隐私限制。 跳过用户。。正在执行下一个")
            del users[n]
            n+=1
        except:
            # traceback.print_exc()
            del users[n]
            n += 1
            errmsg = traceback.format_exc()
            if errmsg.find("One of the users you tried to add is already in too many channels/supergroups") != -1:
                print("您尝试添加的用户之一已经在太多频道/超级组中")
                continue
            if errmsg.find("FloodWaitError") != -1:
                print("临时禁用")
                index += 1
                init_tg_connect()
                continue
            print(errmsg)
            # print("Unexpected Error")
            error_count += 1
            if error_count > 250:
                save_unprocessed(users)
                sys.exit('too many errors')
            continue
def list_users_in_group():
    chats = []
    last_date = None
    chunk_size = 200
    groups = []

    result = client(GetDialogsRequest(
        offset_date=last_date,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=chunk_size,
        hash=0
    ))
    chats.extend(result.chats)

    for chat in chats:
        try:
            print(chat)
            groups.append(chat)
            # if chat.megagroup== True:
        except:
            continue

    print('Choose a group to scrape members from:')
    i = 0
    for g in groups:
        print(str(i) + '- ' + g.title)
        i += 1

    g_index = input("Enter a Number: ")
    target_group = groups[int(g_index)]

    print('\n\nGrupo elegido:\t' + groups[int(g_index)].title)

    print('Fetching Members...')
    all_participants = []
    all_participants = client.get_participants(target_group, aggressive=True)

    print('Saving In file...')
    with open("members-" + re.sub("-+", "-", re.sub("[^a-zA-Z]", "-", str.lower(target_group.title))) + ".csv", "w",
              encoding='UTF-8') as f:
        writer = csv.writer(f, delimiter=",", lineterminator="\n")
        writer.writerow(['username', 'user id', 'access hash', 'name', 'group', 'group id'])
        for user in all_participants:
            if user.username:
                username = user.username
            else:
                username = ""
            if user.first_name:
                first_name = user.first_name
            else:
                first_name = ""
            if user.last_name:
                last_name = user.last_name
            else:
                last_name = ""
            name = (first_name + ' ' + last_name).strip()
            writer.writerow([username, user.id, user.access_hash, name, target_group.title, target_group.id])
    print('Members scraped successfully.')


def printCSV():
    input_file = sys.argv[1]
    users = []
    with open(input_file, encoding='UTF-8') as f:
        rows = csv.reader(f, delimiter=",", lineterminator="\n")
        next(rows, None)
        for row in rows:
            user = {}
            user['username'] = row[0]
            user['id'] = int(row[1])
            user['access_hash'] = int(row[2])
            users.append(user)
            print(row)
            print(user)
    sys.exit('FINITO')


def save_unprocessed(data):
    with open("members-" + re.sub("-+", "-", re.sub("[^a-zA-Z]", "-","data.csv", "w", encoding='UTF-8'))) as f:
        writer = csv.writer(f, delimiter=",", lineterminator="\n")
        writer.writerow(['username', 'user id', 'access hash'])
        for u in data:
            writer.writerow([u["username"], u["id"], u["access_hash"]])


# print('Fetching Members...')
# all_participants = []
# all_participants = client.get_participants(target_group, aggressive=True)
read_api_hash_file()
init_tg_connect()
print('What do you want to do:')
mode = int(input("Enter \n1-获取群组里的用户\n2-从CSV文件导入用户到群组 (CSV 必须作为参数传递给脚本）\n3-显示CSV\n\n请选择:  "))

if mode == 1:
    list_users_in_group()
elif mode == 2:
    add_users_to_group()
elif mode == 3:
    printCSV()
