from modules.utils import sleeping, logger, sleep
from modules import *
import settings


def run_accs():
    while True:
        try:
            module_data = db.get_random_module()

            if module_data == 'No more accounts left':
                logger.success(f'All accounts done.')
                return 'Ended'

            # initialize
            wallet = Wallet(privatekey=module_data["privatekey"], db=db)

            # proccessing balance
            if wallet.get_balance(chain_name='linea', human=True) < settings.MIN_LINEA_BALANCE:
                wallet.okx_withdraw()

            # run module
            logger.info(f'[•] Web3 | {wallet.address} | Starting "{module_data["module_name"].lower()}"')
            globals()[module_data["module_name"]](wallet=wallet)  # probably using `globals` is a lame way

        except Exception as err:
            logger.error(f'{wallet.address} | Account error: {err}')
            db.append_report(privatekey=wallet.privatekey, text=str(err), success=False)

        finally:
            if type(module_data) == dict:
                if module_data['last']:
                    reports = db.get_account_reports(privatekey=wallet.privatekey)
                    TgReport().send_log(logs=reports)

                sleeping(settings.SLEEP_AFTER_TX)  # задержка между модулями


def choose_mode():
    print("\nSelect the operation mode:")
    print("1. Create Database")
    print("2. Run")
    while True:  # Keep asking until the user makes a valid choice
        try:
            choice = int(input("Enter your choice (1-2): "))
            if choice == 1:
                return 'Delete and create new'
            elif choice == 2:
                return 'Run'
            else:
                print("Invalid choice, please enter 1 or 2.")
        except ValueError:
            print("Invalid input, please enter a numerical value.")


if __name__ == '__main__':
    db = DataBase()

    while True:
        mode = choose_mode()
        match mode:
            case 'Delete and create new':
                db.create_modules()
            case 'Run':
                if run_accs() == 'Ended': break
                print('')

    sleep(0.1)
    input('\n > Exit')
