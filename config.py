import os
from rrmng.rrmngmnt import Host, RootUser

ROOT_USER = "root"
LOCALHOST_LOGS_PATH = os.path.expanduser("~/tmp/bug_hunter_logs")
SHORT_LOGS_DIR = "/short_logs"
LOCAL_ROOT_PASSWORD = localhost_pass"

# Slave/local host
SLAVE_HOST = Host("127.0.0.1")
SLAVE_HOST.users.append(RootUser(LOCAL_ROOT_PASSWORD))
FULL_PERMISSIONS = "777"