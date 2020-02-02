#!python3
import os
import pytz
import datetime

TIMEZONE = pytz.timezone('Asia/Shanghai')
TEST_PHASES = [
    'Semantic Check',
    'Code Generation',
    'Optimization'
]