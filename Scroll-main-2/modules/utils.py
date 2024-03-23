from inspect import getsourcefile
from random import randint
from requests import post
from loguru import logger
from time import sleep
from tqdm import tqdm
import sys
import ctypes
import os


logger.remove()
logger.add(sys.stderr, format="<white>{time:HH:mm:ss}</white> | <level>{message}</level>")
windll = ctypes.windll if os.name == 'nt' else None # for Mac users


class WindowName:
    def __init__(self, accs_amount):
        try: self.path = os.path.abspath(getsourcefile(lambda: 0)).split("\\")[-2]
        except: self.path = os.path.abspath(getsourcefile(lambda: 0)).split("/")[-2]

        self.accs_amount = accs_amount
        self.accs_done = 0
        self.modules_amount = 0
        self.modules_done = 0

        self.update_name()

    def update_name(self):
        if os.name == 'nt':
            windll.kernel32.SetConsoleTitleW(f'Scroll [{self.accs_done}/{self.accs_amount}] | {self.path} | [{self.modules_done}/{self.modules_amount}]')

    def update_accs(self):
        self.accs_done += 1
        self.modules_amount = 0
        self.modules_done = 0
        self.update_name()

    def update_modules(self):
        self.modules_done += 1
        self.update_name()

    def set_modules(self, modules_amount: int):
        self.modules_amount = modules_amount
        self.update_name()


class TgReport:
    def __init__(self):
        self.logs = ''


    def update_logs(self, text: str):
        self.logs += f'{text}\n'


    def send_log(self, wallet, window_name):
        notification_text = f'[{window_name.accs_done}/{window_name.accs_amount}] <i>{wallet.address}</i>\n\n{self.logs}\n\n'
        if wallet.error: notification_text += wallet.error

        texts = []
        while len(notification_text) > 0:
            texts.append(notification_text[:1900])
            notification_text = notification_text[1900:]



def sleeping(*timing):
    if type(timing[0]) == list: timing = timing[0]
    if len(timing) == 2: x = randint(timing[0], timing[1])
    else: x = timing[0]
    for _ in tqdm(range(x), desc='sleep ', bar_format='{desc}: {n_fmt}/{total_fmt}'):
        sleep(1)
