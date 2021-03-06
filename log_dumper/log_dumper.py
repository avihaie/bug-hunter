import logging
import argparse
import os

from rrmng.rrmngmnt.host import Host
from rrmng.rrmngmnt.user import RootUser
import helpers
import global_helpers
import config


LOCAL_HOST = Host("127.0.0.1")

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
    """

    def __init__(
        self,  hosts_ips, passwords, usernames=None, logs=None,
        tail_lines=1000, localhost_pass=None
    ):
        self.hosts_ips = hosts_ips
        self.passwords = passwords
        self.usernames = usernames
        self.logs = logs
        self.tail_lines = tail_lines
        self.localhost_pass = localhost_pass

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

    def collect_logs(self, remote_host, remote_logs_path, full_path):
        """
        Collect logs from remote hosts back to one directory in localhost
        """
        logger.info(
            "Logs will be collected to the following directory %s", full_path
        )
        LOCAL_HOST.users.append(RootUser(self.localhost_pass))
        # Copy log to the localhost directory

        for log in remote_logs_path:
            assert remote_host.fs.transfer(
                path_src=log,
                target_host=LOCAL_HOST,
                path_dst=full_path
            )

    def hosts_components_version(self, executor):
        """
        Find the selected components versions on all hosts

        :returns component,version tuple
        """
        search_components = []
        versions = []
        found_components = []

        # Get rid of duplicated logs
        logs = set(self.logs)

        # Find all software components from the logs
        for log in logs:
            search_components.append(log.split("/")[3])

        # Check per each host all components versions and add it to the hosts_components_versions_dict
        for component in search_components:
            cmd = "rpm -qa | grep ^%s-[0-9]" % component

            logger.info("running command %s", cmd)
            rc, out, err = executor.run_cmd(cmd.split())
            if rc:
                logger.error("command %s failed\noutput=%s\n,err=%s\n" % (cmd, out, err))
                logger.error("Component '%s' was not found on remote host", component)


            else:
                logger.info("component %s version is %s", component, out)
                versions.append(out.rstrip("\n\r"))
                found_components.append(component)

        return zip(found_components, versions)


def dump_hosts_logs(hosts_ips, passwords, usernames, logs, tail_lines, localhost_pass, full_path):
    """

    :param hosts_ips:
    :param passwords:
    :param usernames:
    :param logs:
    :param tail_lines:
    :param localhost_pass:
    :param full_path:

    :return: Tuple of collected versions of components per host as key
    """

    components_version_full_list = []
    remote_hosts_logs_dict = {}
    host_executors = []

    logd_obj = LogDumper(
        hosts_ips=hosts_ips, passwords=passwords, usernames=usernames,
        logs=logs[0], tail_lines=tail_lines, localhost_pass=localhost_pass
    )
    # Get host executors per host
    for host_ip, password, username, logs in zip(
        logd_obj.hosts_ips, logd_obj.passwords, logd_obj.usernames, logd_obj.logs
    ):
        remote_hosts_logs_dict[host_ip] = {
            'password': password,
            'username': username,
            'logs': logs,
            'tail_lines': logd_obj.tail_lines,
        }
        logger.info("Host logs dict looks like %s", remote_hosts_logs_dict)
        host_executors.append(
            helpers.get_host_executor(host_ip, password, username)
        )
        logger.info("Dumping logs %s on host ip %s", remote_hosts_logs_dict[host_ip]['logs'], host_ip)
        cut_logs_path = logd_obj.dump_host_logs(
            host_executors[-1], [remote_hosts_logs_dict[host_ip]['logs']], remote_hosts_logs_dict[host_ip]['tail_lines']
        )
        cut_logs_path.extend([remote_hosts_logs_dict[host_ip]['logs']])

        # Copy dumped logs back to localhost
        logger.info("Collect logs %s back to localhost", cut_logs_path)
        remote_host = Host(host_ip)
        remote_host.users.append(RootUser(password))

        # Collect logs back to localhost
        logd_obj.collect_logs(remote_host=remote_host, remote_logs_path=cut_logs_path, full_path=full_path)

        # Collect components versions
        logger.info("Collect host %s components versions", host_ip)
        components_version_tuple = logd_obj.hosts_components_version(executor=host_executors[-1])
        components_version_full_list.append(components_version_tuple)

    return components_version_full_list





def main():
    """
        In case of manual execution -
        (files_to_watch,ips,usernames,passwords,linesnumber,localhostpass)

            - ip: the remote machine IP of the machine that the
              logs dump should exec on
            - username/password: remote host authentication of the machine that
              the logs dump should exec on
            - files_to_dump: absolute path of the file that should be dumped (
              start with "/") of the machine that the
              logs dump should exec on

        Options -
            * -m, --machine :followed by ip,username, password, log/s to dump on  the remote
              machines (e.g. -m 10.0.0.0 root P@SSW0RD  /var/log/log1  -m 10.0.0.1 root P@SSW0RD  /var/log/log2))
              each machine should be preceded by -m separately
            * -l,--linesnumber:  option that is followed by the integer value
              of the lines taken from the end of the selected log file
              (e.g. -f /log/vdsm/vdsm.log -l 1000)
            * -p,--localhostpass:  option that followed by the string value of
              the password of the localhost.
              (e.g. -p "password")

        Example for manual usage:
        python log_dumper/log_dumper.py -m 10.0.0.1 root password /var/log/vdsm/vdsm.log /var/log/vdsm/vdsm2.log -m 10.0.0.2 root password /var/log/vdsm/vdsm3.log -l 1000 -p "1234"

        """
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s')

    parser = argparse.ArgumentParser(
        description='This function can be used to dump log files for remote '
                    'hosts with a select number of line from the end'
    )

    parser.add_argument("-m", "--machines", action="append", dest="machines",
                        help="remote machine to dump logs on '-m' "
                             "followed by ip,username , password, logs_to_dump,"
                             " If you want several machines add an addtional -m option",
                        metavar="machine-ip username password logs",  nargs='+')

    parser.add_argument("-l", "--linesnumber", action="store", type=int,
                        dest="line_numbers",
                        help="cut logs for the last N lines number",
                        default=1000)

    parser.add_argument("-p", "--localhostpass", action="store", type=str,
                        dest="localhost_pass",
                        help="password of the localhost on '-p' followed by "
                             "the localhost password",
                        )

    parser.add_argument("-f", "--localhostfullpath", action="store", type=str,
                        dest = "localhost_logs_full_path",
                        help = "logs directory path on the localhost , '-f' followed by "
                               "full path of logs directory , i.e default is: '~/tmp/bug_hunter_logs'",
                        default=global_helpers.create_localhost_logs_dir(config.LOCALHOST_LOGS_PATH),
                        )




    options = parser.parse_args()
    if options.machines:
        machines = options.machines
        hosts_ips = [machine[0] for machine in machines]
        usernames = [machine[1] for machine in machines]
        passwords = [machine[2] for machine in machines]
        logs = [machine[3:] for machine in machines]
        tail_lines = options.line_numbers
        localhost_pass = options.localhost_pass
        full_path = options.localhost_logs_full_path
    else:
        raise RuntimeError("Missing arguments! usage : %s", parser.parse_args(['-h']))

    logger.info("start dumping logs...")
    config.LOCAL_ROOT_PASSWORD = localhost_pass
    hosts_components_version = dump_hosts_logs(
        hosts_ips=hosts_ips, passwords=passwords, usernames=usernames, logs=logs,
        tail_lines=tail_lines, localhost_pass=localhost_pass, full_path=full_path
    )
    logger.info(
        "Done !!!\n%s last lines and full version logs %s copied from hosts_ips %s to localhost",
        tail_lines, logs, hosts_ips
    )
    logger.info("hosts_components_version are: %s", hosts_components_version)


if __name__ == '__main__':
    main()
