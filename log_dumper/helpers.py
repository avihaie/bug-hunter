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
