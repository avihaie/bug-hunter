import datetime
import os
import getpass

import config
from rrmng.rrmngmnt.host import Host
from rrmng.rrmngmnt.user import User


def get_host_resource(ip, password, username=None):
    """
    Return remote resource with given username/password on given ip
    :param ip: host ip
    :type: ip: str
    :param username: host username, if None using root user
    :type username: str
    :param password: user's password
    :type: password: str
    :return: Host with root user
    :rtype: Host
    """
    host = Host(ip)
    _user = username if username else config.ROOT_USER
    host.users.append(User(_user, password))
    return host


def get_host_executor(ip, password, username=None, use_pkey=False):
    """
    :param ip: Host ip
    :type: ip: str
    :param password: User's password
    :type: password: str
    :param username:  Host username, if None using root user
    :type username: str
    :param use_pkey: Use ssh private key to connect without password
    :type use_pkey: bool
    :return: RemoteExecutor with given username
    :rtype: RemoteExecutor
    """
    _user = username if username else config.ROOT_USER
    user = User(_user, password)
    return get_host_resource(
        ip, password, username
    ).executor(user, pkey=use_pkey)


def create_localhost_logs_dir(local_host_logs_path):
    """
    Collect logs from remote hosts back to one directory in localhost
    """
    # Create directory names after current timestamp
    if not os.path.exists(local_host_logs_path):
        os.mkdir(local_host_logs_path)
    dir_name = datetime.datetime.now().strftime("%d%m%y_%H:%M:%S")
    full_path = local_host_logs_path + "/" + dir_name
    localhost_user = localhost_group = getpass.getuser()
    print "localhost_user and group is %s" % localhost_user
    try:
        config.SLAVE_HOST.fs.mkdir(full_path)
        config.SLAVE_HOST.fs.chmod(full_path, config.FULL_PERMISSIONS)
        config.SLAVE_HOST.fs.chown(full_path, localhost_user, localhost_group)

    except Exception as e:
        print "Issue %s occured while creating/chmod dir %s" % (e, full_path)
    return full_path

def create_localhost_short_logs_dir(local_host_logs_path, lines):
    """
    Create dir for short logs only and move short logs to the new location at localhsot
    """
    short_logs_full_path = local_host_logs_path + config.SHORT_LOGS_DIR
    config.SLAVE_HOST.fs.mkdir(short_logs_full_path)
    config.SLAVE_HOST.fs.chmod(short_logs_full_path, config.FULL_PERMISSIONS)
    file_list = config.SLAVE_HOST.fs.listdir(local_host_logs_path)
    short_logs_names = [file.encode('utf-8') for file in file_list if file.endswith(".log" + str(lines))]
    for short_log_name in short_logs_names:
        config.SLAVE_HOST.fs.move(local_host_logs_path + "/" + short_log_name, short_logs_full_path + "/" + short_log_name)


def chmod_files_directories(dir_path):
    """
    Change permissions recursively of all files and directories in a selected directory
    """
    for root, dirs, files in os.walk(dir_path):
        for f in files:
            config.SLAVE_HOST.fs.chmod(os.path.join(root, f), config.FULL_PERMISSIONS)