from random import choice, randint
from os import path, mkdir
import json

from modules.utils import logger, get_address, WindowName
from settings import LINEA_QUESTS, SHUFFLE_WALLETS


class DataBase:
    def __init__(self):
        self.modules_bd_name = 'databases/modules.json'
        self.report_bd_name = 'databases/report.json'
        self.window_name = None

        # create db's if not exists
        if not path.isdir(self.modules_bd_name.split('/')[0]):
            mkdir(self.modules_bd_name.split('/')[0])

        if not path.isfile(self.modules_bd_name):
            with open(self.modules_bd_name, 'w') as f: f.write('[]')
        if not path.isfile(self.report_bd_name):
            with open(self.report_bd_name, 'w') as f: f.write('{}')

        amounts = self.get_amounts()
        logger.info(f'Loaded {amounts["modules_amount"]} modules for {amounts["accs_amount"]} accounts\n')


    def create_modules(self):
        with open('privatekeys.txt') as f: private_keys = f.read().splitlines()

        with open(self.report_bd_name, 'w') as f: f.write('{}')  # clear report db

        static_modules = [quest_name for quest_name in LINEA_QUESTS.keys() if LINEA_QUESTS[quest_name]]

        new_modules = {}
        shuffled_modules = {}
        for pk in private_keys:
            new_modules[pk] = {"modules": static_modules}

        p_keys = list(new_modules.keys())
        while p_keys:
            p_key = p_keys.pop(randint(0, len(p_keys)-1))
            shuffled_modules[p_key] = new_modules[p_key]

        with open(self.modules_bd_name, 'w', encoding="utf-8") as f: json.dump(shuffled_modules, f)

        amounts = self.get_amounts()
        logger.info(f'Created Database for {amounts["accs_amount"]} accounts with {amounts["modules_amount"]} modules!\n')


    def get_amounts(self):
        with open(self.modules_bd_name, encoding="utf-8") as f: modules_bd = json.load(f)
        modules_len = sum([len(modules_bd[acc]["modules"]) for acc in modules_bd])

        if self.window_name == None: self.window_name = WindowName(accs_amount=len(modules_bd))
        else: self.window_name.accs_amount = len(modules_bd)
        self.window_name.set_modules(modules_amount=modules_len)

        return {'accs_amount': len(modules_bd), 'modules_amount': modules_len}


    def get_random_module(self):
        last = False
        with open(self.modules_bd_name, encoding="utf-8") as f: modules_db = json.load(f)
        if not modules_db: return 'No more accounts left'

        if SHUFFLE_WALLETS: privatekey = choice(list(modules_db.keys()))
        else: privatekey = list(modules_db.keys())[0]
        module_name = choice(modules_db[privatekey]["modules"])

        modules_db[privatekey]["modules"].remove(module_name)

        if not modules_db[privatekey]["modules"]: # if no modules left for this account
            self.window_name.add_acc()
            del modules_db[privatekey]
            last = True

        self.window_name.add_module()

        with open(self.modules_bd_name, 'w', encoding="utf-8") as f: json.dump(modules_db, f)

        return {'privatekey': privatekey, 'module_name': module_name, 'last': last}


    def append_report(self, privatekey: str, text: str, success: bool = None):
        status_smiles = {True: '✅ ', False: "❌ ", None: ""}

        with open(self.report_bd_name, encoding="utf-8") as f: report_bd = json.load(f)

        if not report_bd.get(privatekey): report_bd[privatekey] = {'texts': [], 'success_rate': [0, 0]}

        report_bd[privatekey]["texts"].append(status_smiles[success] + text)
        if success != None:
            report_bd[privatekey]["success_rate"][1] += 1
            if success == True: report_bd[privatekey]["success_rate"][0] += 1

        with open(self.report_bd_name, 'w') as f: json.dump(report_bd, f)


    def get_account_reports(self, privatekey: str):
        with open(self.report_bd_name, encoding="utf-8") as f: report_bd = json.load(f)

        if report_bd.get(privatekey):
            account_reports = report_bd[privatekey]
            del report_bd[privatekey]

            with open(self.report_bd_name, 'w', encoding="utf-8") as f: json.dump(report_bd, f)

            logs_text = '\n'.join(account_reports['texts'])
            tg_text = f'[{self.window_name.accs_done}/{self.window_name.accs_amount}] {get_address(pk=privatekey)}\n\n' \
                      f'{logs_text}\n\n' \
                      f'Success rate {account_reports["success_rate"][0]}/{account_reports["success_rate"][1]}'

            return tg_text

        else:
            return f'[{self.window_name.accs_done}/{self.window_name.accs_amount}] {get_address(pk=privatekey)}\n\n' \
                     f'No actions'
