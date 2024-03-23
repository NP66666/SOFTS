from random import randint
from time import sleep
from tqdm import tqdm
from sys import stderr
from loguru import logger

logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white> | <level>{level: <3}</level> | <level>{message}</level>")


def sleeping(*timing):
    if type(timing[0]) == list:
        timing = timing[0]
    if len(timing) == 2:
        x = randint(timing[0], timing[1])
    else:
        x = timing[0]
    for _ in tqdm(range(x), desc='sleep ', bar_format='{desc}: {n_fmt}/{total_fmt}'):
        sleep(1)
