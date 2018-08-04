import datetime
import os
import config

from rrmngmnt.host import Host
from rrmngmnt.user import User


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
    os.mkdir(full_path)
    return full_path
