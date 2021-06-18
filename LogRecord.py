import logging
import time
import os

log = logging.getLogger()
log.setLevel(level)
rq = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
log_path = os.getcwd() + '/Logs/'
logfile = log_path + rq + '.log'

fh = logging.FileHandler(logfile, mode='w')
fh.setLevel(level)

formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
fh.setFormatter(formatter)

ch = logging.StreamHandler()
ch.setFormatter(formatter)

log.addHandler(fh)
log.addHandler(ch)