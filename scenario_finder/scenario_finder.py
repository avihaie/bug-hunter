import smtplib
import logging, os, datetime, socket
import argparse
# from log_dumper.log_dumper import LogDumper
from rrmngmnt.host import Host
from rrmngmnt.user import RootUser

LOCALHOST_LOGS_PATH = os.path.expanduser("~/tmp")
# this monstrous thing extracts localhost ip
LOCAL_HOST = Host( [l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]
                    if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), s.getsockname()[0],
                    s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) if l][0][0] )

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - ''%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


class ScenarioFinder:
    """
    """
    def __init__(self,  hosts_ips, passwords, usernames=None, logs=None, tail_lines=1000, localhost_pass=None):
        self.hosts_ips = hosts_ips
        self.passwords = passwords
        self.usernames = usernames
        self.logs = logs
        self.tail_lines = tail_lines
        self.localhost_pass = localhost_pass


    def collect_logs(self):
        """
        Collect logs from remote host back to one directory in localhost
        """
        # Create directory names after current timestamp
        if not os.path.exists(LOCALHOST_LOGS_PATH):
            os.mkdir(LOCALHOST_LOGS_PATH)
        dir_name = datetime.datetime.now().strftime("%d%m%y_%H:%M:%S")
        full_path = LOCALHOST_LOGS_PATH + "/" + dir_name
        os.mkdir(full_path)
        logger.info("Logs will be collected to the following directory %s", full_path)
        LOCAL_HOST.users.append(RootUser(self.localhost_pass))

        # Copy log to the localhost directory
        for host_ip, password, username, log in zip(self.hosts_ips, self.passwords, self.usernames, self.logs):
            remote_host = Host(host_ip)
            remote_host.users.append(RootUser(password=password))
            assert remote_host.fs.transfer(
                path_src=log,
                target_host=LOCAL_HOST,
                path_dst=full_path)


def main():
    """
    In case of manual execution -
    (event,event_details,mail_source,mail_user,mail_password)

    e.g python notifier.py -e Exception -d "NullPointerException" -u "testuser@gmail.com" -p "123456" -o
    "storage-ge4-test.scl.lab.tlv.redhat.com" -t "TestCase18145"

        - event: summery of the event
        - event_details: details of the event
        - mail_user = mail_source: email source address that will appear on the sent mail triggered after the event
        - mail_password: email password of the source address

    Options -
        * -e, --event : summery of the event (e.g. -e "Exception caught" )
        * -d, --event_details: event details (e.g. -d "NullPointerException ...")
        * -u, --mail_user : email user which is equal to email itself (e.g. -u "test@gmail.com")
        * -p, --mail_password : email password (e.g. -p "123456")
        * -o, --host_name : host name the issue occurred on (e.g. -p "storage-ge4-test.scl.lab.tlv.redhat.com")
        * -t, --test_name : name of the test (e.g. -e 'TestCase18145')

    """
    usage = "usage: %prog [options] arg1 arg2"
    parser = argparse.ArgumentParser(description='This functionality parses engine events')
    parser.add_argument("-m", "--machines", action="append", dest="machines",
                        nargs=3,
                        help="remote machine to download logs from  '-m' "
                             "followed by ip,username & password",
                        default=[])

    parser.add_argument("-f", "--files", action="append", dest="files_to_download",
                        help="option that followed by the absolute path of the file that need to be downloaded,"
                             " each file should be preceded by -f separately",
                        default=[])

    parser.add_argument("-p", "--localhostpass", action="store", type=str, dest="localhost_pass",
                        help="password of the localhost")

    args = parser.parse_args()
    if len(args.files_to_download) > 0 and len(args.machines):
        machines = args.machines
        hosts_ips = [machine[0] for machine in machines]
        usernames = [machine[1] for machine in machines]
        passwords = [machine[2] for machine in machines]
        log_files = args.files_to_download
        localhost_pass = args.localhost_pass
    else:
        raise RuntimeError("Missing arguments! usage : %s", usage)

    logger.info("start dumping logs...")

    scenario_finder = ScenarioFinder(hosts_ips=hosts_ips, passwords=passwords, logs=log_files, usernames=usernames,
                                     localhost_pass=localhost_pass)
    scenario_finder.collect_logs()

if __name__ == '__main__':
    # Run as a script directly from terminal
    main()
