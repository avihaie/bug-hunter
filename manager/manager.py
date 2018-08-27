import logging
import time
import datetime

import config
import helpers
from log_listener import watch_logs
from log_dumper import dump_hosts_logs
from notifier import notify_via_mail_and_console

# set up logging to file
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - '
           '%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class Manager:
    """
    responsibilities:
    1) Lunch the main script that will trigger bug hunter operation
    2) log-listening to which hosts & logs on those hosts
    3) trigger local/remote dump logs
    4) enable/disable mapping (deep analisys)
    5) fault-handling of log-listener and other operations when host/service was restarted/unavailable

    rhv_manager method will run the main flow for handling an rhv issue
    """

    def __init__(
        self, fault_regex, logs, remote_hosts, remote_users, remote_passwords, timeout=None, localhost_pass=None,
        tail_lines=None, target_mail=None, mail_user=None, mail_password=None, test_name=None , event_regex=None
    ):
        self.fault_regex = fault_regex
        self.logs = logs
        self.remote_hosts = remote_hosts
        self.remote_users = remote_users
        self.remote_passwords = remote_passwords
        self.timeout = timeout
        self.localhost_pass = localhost_pass
        self.tail_lines = tail_lines
        self.test_start_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        self.target_mail = target_mail
        self.mail_user = mail_user
        self.mail_password = mail_password
        self.test_name = test_name
        self.event_regex = event_regex

    @property
    def self.fault_regex(self):
        return self.__fault_regex

    @fault_regex.setter
    def fault_regex(self, fault_regex_val):
        self.__fault_regex = fault_regex_val

    @property
    def logs(self):
        return self.__logs

    @logs.setter
    def logs(self, logs_val):
        self.__logs = logs_val

    @property
    def remote_hosts(self):
        return self.__remote_hosts

    @remote_hosts.setter
    def remote_hosts(self, remote_hosts_val):
        self.__remote_hosts = remote_hosts_val

    @property
    def remote_users(self):
        return self.__remote_users

    @remote_users.setter
    def remote_users(self, remote_users_val):
        self.__remote_users = remote_users_val

    @property
    def remote_passwords(self):
        return self.__remote_passwords

    @remote_passwords.setter
    def remote_passwords(self, remote_passwords_val):
        self.__remote_passwords = remote_passwords_val

    @property
    def timeout(self):
        return self.__timeout

    @timeout.setter
    def timeout(self, timeout_val):
        self.__timeout = timeout_val

    @property
    def localhost_pass(self):
        return self.__localhost_pass

    @localhost_pass.setter
    def localhost_pass(self, localhost_pass_val):
        self.__localhost_pass = localhost_pass_val

    @property
    def tail_lines(self):
        return self.__tail_lines

    @tail_lines.setter
    def tail_lines(self, tail_lines_val):
        self.__tail_lines = tail_lines_val

    @property
    def test_start_time(self):
        return self.__tail_lines

    @test_start_time.setter
    def test_start_time(self, test_start_time_val):
        self.__test_start_time = test_start_time_val
        
    @property
    def event_regex(self):
        return self.__event_regex

    @event_regex.setter
    def event_regex(self, event_regex_val):
        self.__event_regex = event_regex_val

    def _rhv_manager(self):
        test_start_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        logger.info("Starting test monitoring at %s", test_start_time)

        full_path = helpers.create_localhost_logs_dir(config.LOCALHOST_LOGS_PATH)
        logger.info("Local host logs directory set to %s",full_path)

        logger.info("Starting log listener searching for regex %s in logs %s", self.regex, self.logs)
        found_regex, issue_found = watch_logs(
            files_to_watch=self.logs()[1],
            regex=self.fault_regex,
            ip_for_files=self.remote_hosts,
            username=self.remote_users,
            password=self.remote_passwords,
            time_out=-1,
            )

        # TODO: implemet multithreading for 3 threads log_dumper(run serially event_finder,mapper) , notifier , check_env_state
        # TODO: Once all threads are all done run bugzilla reporter
        logger.info("Issue found: %s\n Starting to dump logs to localhost ", issue_found)

        test_logs_path = dump_hosts_logs(
            hosts_ips=self.remote_hosts, passwords=self.remote_passwords, usernames=self.remote_users, logs=self.logs,
            tail_lines=self.tail_lines, localhost_pass=self.localhost_pass, full_path= full_path
        )
        logger.info("Logs dumped to localhost %s", test_logs_path)
        logger.info("Notify of the issue via mail and consule")
        notify_via_mail_and_console(self.fault_regex, found_regex)
        logger.info("Parsing scenario from the log file")
        scenario_finder = ScenarioFinder(
            time_start=self.test_start_time, path_logs=full_path, event_string="EVENT_ID", 
            scenario_result_file_path=full_path)
        scenario_finder.parse_logs()

