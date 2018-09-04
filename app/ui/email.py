from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient import errors
from bs4 import BeautifulSoup
from datetime import datetime as dt, timedelta, timezone
from base64 import b64decode
from time import time
import os
import pytz
from dateutil.tz import tzlocal

now_timestamp = time()
offset = dt.fromtimestamp(now_timestamp) - dt.utcfromtimestamp(now_timestamp)


DIR_PATH = os.path.dirname(os.path.abspath(__file__))
# If modifying these scopes, delete the file token.json.

def query_messages(filter_labels=[], query=''):
    SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
    q = "in:inbox is:unread -category:(promotions OR social)" + query
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(DIR_PATH + '/credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('gmail', 'v1', http=creds.authorize(Http()))
    user_id = 'me'

    msgs = service.users().messages().list(userId='me', labelIds=filter_labels, q=q).execute()['messages']
    return get_messages_from_ids(msgs, user_id, service)


def get_messages_from_ids(msgs, user_id, service):
    msg_list = []
    for msg in msgs:
        temp_dict = {}
        message = service.users().messages().get(userId=user_id, id=msg['id']).execute()
        headers = message['payload']['headers']

        for header in headers:
            if header['name'] == 'Subject':
                temp_dict['subject'] = header['value']
            elif header['name'] == 'Date':
                split = header['value'].split()
                if len(split) > 6:
                    msg_date = ' '.join(split[:6])
                dtime = dt.strptime(msg_date, "%a, %d %b %Y %H:%M:%S %z")
                local_dtime = dtime.astimezone(tzlocal())
                if dt.utcnow().replace(tzinfo=pytz.utc) - dtime < timedelta(hours=24):
                    temp_dict['show_time'] = True
                else:
                    temp_dict['show_time'] = False
                temp_dict['date'] = local_dtime.strftime("%b %d")
                temp_dict['time'] = local_dtime.strftime("%H:%M %p")
            elif header['name'] == 'From':
                split = header['value'].split()
                temp_dict['sender'] = {}
                temp_dict['sender']['name'] = " ".join(split[:-1])
                temp_dict['sender']['email'] = split[-1]
            else:
                pass

        temp_dict['snippet'] = message['snippet']

        try:
            msg_parts = message['payload']['parts']
            data = msg_parts[0]['body']['data']
            clean_data_encoded = data.replace("-", "+").replace("_", "/")
            clean_data_decoded = b64decode(bytes(clean_data_encoded, 'UTF-8'))
            soup = BeautifulSoup(clean_data_decoded, 'html')
            msg_body = soup.body()
            temp_dict['msg_body'] = msg_body
        except Exception as e:
            print("ERROR {} when retrieving email".format(e))

        msg_list.append(temp_dict)
    return msg_list

