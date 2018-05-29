import logging
import argparse
import datetime
import os
import socket
import helpers
import config
from rrmngmnt.host import Host
from rrmngmnt.user import RootUser


LOCALHOST_LOGS_PATH = os.path.expanduser("~/tmp")
SLAVE_HOST = Host("127.0.0.1")
SLAVE_HOST.users.append(RootUser("AVIEf274^&$"))

# set up logging to file
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - '
           '%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class LogDumper:
    """
    LogDumper class, dumps selected logs on remote hosts and copy them to a
    directory on the localhost.
    Each host can choose what files to dump.
    """

    def __init__(
        self,  hosts_ips, passwords, usernames=None, logs=None, tail_lines=1000
    ):
        self.hosts_ips = hosts_ips
        self.passwords = passwords
        self.usernames = usernames
        self.logs = logs
        self.tail_lines = tail_lines

    def dump_host_logs(self, executor, logs=None, tail_lines=1000):
        """
        Dump N number of last lines of selected host logs
        """
        cut_logs_path = []
        for log in logs:
            cut_log = log + str(tail_lines)
            cmd = 'tail -n %s %s > %s' % (tail_lines, log, cut_log)
            logger.info("running command %s", cmd)
            rc, out, err = executor.run_cmd(cmd.split())
            assert not rc, (
                "command %s failed\noutput=%s\n,err=%s\n" % (cmd, out, err)
            )
            logger.info("Dumped log is located at path %s", cut_log)
            cut_logs_path.append(os.path.abspath(cut_log))
        return cut_logs_path

    def collect_logs(self, remote_host, remote_logs_path=None):
        """
        Collect logs from remote host back to one directory in localhost
        """
        # Create directory names after current timestamp
        if not os.path.exists(LOCALHOST_LOGS_PATH):
            os.mkdir(LOCALHOST_LOGS_PATH)
        dir_name = datetime.datetime.now().strftime("%d%m%y_%H:%M:%S")
        full_path = LOCALHOST_LOGS_PATH + "/" + dir_name
        os.mkdir(full_path)
        logger.info(
            "Logs will be collected to the following directory %s", full_path
        )
        # Copy log to the localhost directory
        assert remote_host.fs.transfer(
            path_src=remote_logs_path,
            target_host=SLAVE_HOST,
            path_dst=full_path
        )

    def dump_hosts_logs(self):
        hosts_logs_dict = {}
        host_executors = []
        # Get host executors per host
        for host_ip, password, username, logs in zip(
            self.hosts_ips, self.passwords, self.usernames, self.logs
        ):
            hosts_logs_dict[host_ip] = {
                'password': password,
                'username': username,
                'logs': self.logs,
                'tail_lines': self.tail_lines,
            }
            logger.info("Host logs dict looks like %s", hosts_logs_dict)
            host_executors.append(
                helpers.get_host_executor(host_ip, password, username)
            )

            logger.info("Dumping logs %s on host ip %s", self.logs, host_ip)
            cut_logs_path = self.dump_host_logs(
                host_executors[-1], self.logs, self.tail_lines
            )
            # Copy dumped logs back to localhost
            logger.info("Collect logs %s back to localhost", self.logs)
            remote_host = Host(host_ip)
            remote_host.users.append(RootUser(password))
            self.collect_logs(remote_host=remote_host, remote_logs_path=cut_logs_path[0])


def main():
    """
        In case of manual execution -
        (files_to_watch,ips,usernames,passwords)

        1. in case of remote machine:
            - ip: the remote machine IP
            - username/password: authentication

        2. for all cases:
            - files_to_dump: absolute path of the file that should be dumped (
              start with "/")
            - ip_for_execute_dump: the !!! IP !!! of the machine that the
              logs dump should exec on
            - remote_username: username for the remote  machine
            - remote_password: password for the remote  machine

        Options -
            * -m, --machine :followed by ip,username & password
              (e.g. -m 10.0.0.0 root P@SSW0RD)
              each machine should be preceded by -m separately
            * -f,--files : option that followed by the absolute path of the files
              that need to watch for.
              each file should be preceded by -f separately
              (e.g. -f /var/log/vdsm/vdsm.log -f /tmp/my_log)

        """
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s')

    usage = "usage: %prog [options] arg1 arg2"
    parser = argparse.ArgumentParser(
        description='This function can be used to dump log files for remote '
                    'hosts with a select number of line from the end'
                    )

    parser.add_argument("-m", "--machines", action="append", dest="machines",
                        nargs=3,
                        help="remote machine to dump logs on  '-m' "
                             "followed by ip,username & password",
                        default=[])

    parser.add_argument("-f", "--files", action="append",
                        dest="files_to_dump",
                        help="option that followed by "
                             "the absolute path of the "
                             "file that need dumping, each file should "
                             "be preceded by -f separately",
                        default=[])

    parser.add_argument("-l", "--linesnumber", action="store", type=int,
                        dest="line_numbers",
                        help="cut logs for the last N lines number",
                        default=1000)

    options = parser.parse_args()

    if len(options.files_to_dump) > 0 and len(options.machines):
        machines = options.machines
        hosts_ips = [machine[0] for machine in machines]
        usernames = [machine[1] for machine in machines]
        passwords = [machine[2] for machine in machines]
        logs = options.files_to_dump
    else:
        raise RuntimeError("Missing arguments! usage : %s", usage)

    logger.info("start dumping logs...")
    obj = LogDumper(hosts_ips, passwords, usernames, logs)
    obj.dump_hosts_logs()
    logger.info(
        "Done !!!\n logs %s copied from hosts_ips %s to localhost",
        obj.hosts_ips, obj.logs
    )

if __name__ == '__main__':
    main()
