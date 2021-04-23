from elastalert.alerts import Alerter, BasicMatchString

from . import return_index

import requests
import json
import warnings

from requests.auth import HTTPProxyAuth
from requests.exceptions import RequestException
from elastalert.util import EAException
from elastalert.util import elastalert_logger

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)

class TelegramAlerter(Alerter):
    """ Send a Telegram message via bot api for each alert """
    required_options = frozenset(['telegram_bot_token', 'telegram_room_id'])

    def __init__(self, rule):
        super(TelegramAlerter, self).__init__(rule)
        self.telegram_bot_token = self.rule['telegram_bot_token']
        self.telegram_room_id = self.rule['telegram_room_id']
        self.telegram_api_url = self.rule.get('telegram_api_url', 'api.telegram.org')
        self.url = 'https://%s/bot%s/%s' % (self.telegram_api_url, self.telegram_bot_token, "sendMessage")
        self.telegram_proxy = self.rule.get('telegram_proxy', None)
        self.telegram_proxy_login = self.rule.get('telegram_proxy_login', None)
        self.telegram_proxy_password = self.rule.get('telegram_proxy_pass', None)
        self.telegram_use_markdown = self.rule.get('telegram_use_markdown', 'default')
        self.telegram_limit_option = self.rule.get('telegram_limit_option', 'default')

    def alert(self, matches):
        return_index_class = return_index.ReturnIndex()
        if self.telegram_use_markdown == 'custom':
            body = '⚠ *%s* ⚠ \n' % (self.create_title(matches))
            telegram_lim_end = '----------------------------------------'
            telegram_lim_check = 4095

            for match in matches:
                body += str(BasicMatchString(self.rule, match))
                # Separate text of aggregated alerts with dashes
                if len(matches) > 1:
                    body += '\n%s\n' % telegram_lim_end

            if len(body) > telegram_lim_check:
                return_index_class.send_to_es(body, option=self.telegram_limit_option)
                telegram_lim_search = telegram_lim_check
                while telegram_lim_search > 0:
                    telegram_lim_40 = body[(telegram_lim_search-40):telegram_lim_search]
                    if telegram_lim_40 == telegram_lim_end:
                        body = body[0:(telegram_lim_search-40)] + "\n *message was cropped according to telegram limits!* \n"
                        break
                    telegram_lim_search -= 1
        elif self.telegram_use_markdown == 'default':
            body = '⚠ *%s* ⚠ ```\n' % (self.create_title(matches))
            for match in matches:
                body += str(BasicMatchString(self.rule, match))
                # Separate text of aggregated alerts with dashes
                if len(matches) > 1:
                    body += '\n----------------------------------------\n'
            if len(body) > 4095:
                return_index_class.send_to_es(body, option=self.telegram_limit_option)
                body = body[0:4000] + "\n⚠ *message was cropped according to telegram limits!* ⚠"
            body += ' ```'

        headers = {'content-type': 'application/json'}
        # set https proxy, if it was provided
        proxies = {'https': self.telegram_proxy} if self.telegram_proxy else None
        auth = HTTPProxyAuth(self.telegram_proxy_login, self.telegram_proxy_password) if self.telegram_proxy_login else None
        payload = {
            'chat_id': self.telegram_room_id,
            'text': body,
            'parse_mode': 'markdown',
            'disable_web_page_preview': True
        }

        try:
            response = requests.post(self.url, data=json.dumps(payload, cls=DateTimeEncoder), headers=headers, proxies=proxies, auth=auth)
            warnings.resetwarnings()
            response.raise_for_status()
        except RequestException as e:
            raise EAException("Error posting to Telegram: %s. Details: %s" % (e, "" if e.response is None else e.response.text))

        elastalert_logger.info(
            "Alert sent to Telegram room %s" % self.telegram_room_id)

    def get_info(self):
        return {'type': 'telegram',
                'telegram_room_id': self.telegram_room_id}
