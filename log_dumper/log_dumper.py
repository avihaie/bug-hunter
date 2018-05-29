import logging
import argparse

import helpers
import config

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
    Dumper class, dumps trimmed requested selected logs on remote hosts.
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
        for log in logs:
            cut_log = log + str(tail_lines)
            cmd = 'tail -n %s %s > %s' % (tail_lines, log, cut_log)
            logger.info("running command %s", cmd)
            rc, out, err = executor.run_cmd(cmd.split())
            assert not rc, (
                "command %s failed\noutput=%s\n,err=%s\n" % (cmd, out, err)
            )
            logger.info("Dumped log is located at path %s", cut_log)

    def dump_hosts_logs(
        self, hosts_ips, passwords, usernames=None, logs=None, tail_lines=1000
    ):
        hosts_logs_dict = {}
        host_executors = []
        # Get host executors per host
        for host_ip, password, username in zip(hosts_ips, passwords, usernames):
            hosts_logs_dict[host_ip] = {
                'password': password,
                'username': username,
                'logs': logs,
                'tail_lines': tail_lines
            }
            logger.info("Host logs dict looks like %s", hosts_logs_dict)
            host_executors.append(
                helpers.get_host_executor(host_ip, password, username)
            )
            logger.info("Dumping logs %s on host ip %s", logs, host_ip)
            self.dump_host_logs(
                host_executors[-1], logs, tail_lines
            )


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
                        default=[(None, None, None)])

    parser.add_argument("-f", "--file", action="append",
                        dest="files_to_dump",
                        help="option that followed by "
                             "the absolute path of the "
                             "file that need dumping, each file should "
                             "be preceded by -f separately",
                        default=[])

    parser.add_argument("-l", "--linesnumber", action="store", type=int,
                        dest="line_numbers",
                        help="cut logs for the last N lines number")

    options = parser.parse_args()

    if len(options.files_to_watch) > 0 and len(options.machines):
        machines = options.machines
        hosts_ips = [machine[0] for machine in machines]
        usernames = [machine[1] for machine in machines]
        passwords = [machine[2] for machine in machines]

        logs = options.files_to_dump
    else:
        raise RuntimeError("Missing arguments! usage : %s", usage)

    logger.info("start dumping logs...")
    obj = LogDumper(hosts_ips, passwords, usernames, logs)
    obj.dump_hosts_logs(hosts_ips, passwords, usernames, logs)
    logger.info("Done !!!")

if __name__ == '__main__':
    main()
