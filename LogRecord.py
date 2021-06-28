import logging
import time
import os

_level_ = logging.DEBUG


log = logging.getLogger()
log.setLevel(_level_)
rq = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
log_path = os.getcwd() + '/Logs/'
logfile = log_path + rq + '.log'

fh = logging.FileHandler(logfile, mode='w', encoding='utf-8')
fh.setLevel(_level_)

formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
fh.setFormatter(formatter)

ch = logging.StreamHandler()
ch.setFormatter(formatter)

log.addHandler(fh)
log.addHandler(ch)