import logging
import time
import datetime
from threading import Thread
import yaml

import config
import global_helpers
from listener.log_listener import watch_logs
from log_dumper.log_dumper import dump_hosts_logs
from notifier.notifier import notify_via_mail_and_console
from scenario_finder.scenario_finder import ScenarioFinder
from env_state.env_state import get_resources_stats
from bugzilla_report_maker.bugzilla_report_maker import bugzilla_report_maker

# set up logging to file
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(threadName)s '
           '%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class Manager:
    """
    responsibilities:
    1. Lunch the main script that will trigger bug hunter operation Rhv/other flow.
    2. Log-listening to which hosts & logs on those hosts.
    3. Collect relevant logs and fetch them to localhost.
    4. Notify via mail and consule when an issue occurs.
    5. Check the enviroment state staring the test and also after an issue occurs.
    6. Create a bugzilla ready report.
    7. enable/disable mapping (deep analisys) - TBD
    8. fault-handling of log-listener and other operations when host/service was restarted/unavailable - TBD

    rhv_manager method will run the main flow for handling an rhv issue, other(openstack,CNV ) currently are TBD.
    """

    def __init__(
        self, fault_regex, logs, remote_hosts, remote_users, remote_passwords, timeout=None, localhost_pass=None,
        tail_lines=None, target_mail=None, mail_user=None, mail_password=None, test_name=None , env_state_uri=None,
        env_state_pass=None
    ):
        self.fault_regex = fault_regex
        # Logs are a list of lists , each list represent logs we require in each host.
        # f.e :[['/var/log/vdsm/vdsm.log'], ['/var/log/ovirt-engine/engine.log']]
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
        self.env_state_uri = env_state_uri
        self.env_state_pass = env_state_pass

    @property
    def fault_regex(self):
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


    def _rhv_manager(self):
        test_start_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        logger.info("Starting test monitoring at %s", test_start_time)

        full_path = global_helpers.create_localhost_logs_dir(config.LOCALHOST_LOGS_PATH)
        logger.info("Local host logs directory set to the following path: %s", full_path + "/" + "env_state_start")

        logger.info("Check the enviroment state at the start of the test")
        get_resources_stats(engine_uri=self.env_state_uri, engine_pass=self.env_state_pass,
                            results_path=full_path + "/" + "env_state_start")

        logger.info("Starting log listener searching for regex %s in logs %s", self.fault_regex, self.logs[0][0])
        found_regex, issue_found = watch_logs(
            files_to_watch=self.logs[0][0],
            regex=self.fault_regex,
            ip_for_files=self.remote_hosts[0],
            username=self.remote_users[0],
            password=self.remote_passwords[0],
            time_out=-1,
            )
        logger.info("Issue found: %s\n Starting to dump logs to localhost ", found_regex)

        components_version_full_list = dump_hosts_logs(
            hosts_ips=self.remote_hosts, passwords=self.remote_passwords, usernames=self.remote_users, logs=self.logs,
            tail_lines=self.tail_lines, localhost_pass=self.localhost_pass, full_path= full_path
        )
        logger.info("Logs dumped to localhost path: %s", full_path)
        logger.info("Moving short logs to dedicated folder")
        global_helpers.create_localhost_short_logs_dir(full_path, self.tail_lines)
        logger.info("Notify of the issue via mail and console")

        t1 = Thread(target=notify_via_mail_and_console, args=(
                self.fault_regex, found_regex, self.target_mail,self.mail_user, self.mail_password,
                self.remote_hosts[0], self.test_name, full_path
        ))
        t2 = Thread(target=get_resources_stats, args=(
            self.env_state_uri, self.env_state_pass, full_path + "/" + "env_state_at_issue")
        )

        logger.info("Starting 2 threads concurrently with the scenario finder as follows:")
        logger.info("Notify of the issue via mail and console done on thread name %s", t1.getName())
        logger.info("Check the environment state when the issue occurred done on thread named %s", t2.getName())

        t1.start()
        t2.start()

        logger.info("Parsing scenario from the log file")
        event_file_path = full_path + "/" + "events"
        global_helpers.chmod_files_directories(full_path)
        scenario_finder_obj = ScenarioFinder(
            time_start=self.test_start_time, path_logs=full_path, event_string="EVENT_ID",
            scenario_result_file_path=event_file_path)
        scenario_finder_obj.parse_logs()

        t1.join()
        t2.join()

        logger.info("All threads are done, now we can start creating bugzilla report")
        logger.info("Creating bugzilla report in file %s")
        bugzilla_report_maker_ob = bugzilla_report_maker(
            logs_path=full_path, issue_found=found_regex, test_name=self.test_name,
            components_versions=components_version_full_list, events_file_path=event_file_path
        )
        bugzilla_report_maker_ob.create_bugzilla_file()


def run_rhv_manager(yaml_path):
    conf = yaml.load(open(yaml_path))
    manager_obj = Manager(
        fault_regex=conf['fault_regex'], logs=[conf['logs']], remote_hosts=conf['remote_hosts'],
        remote_users=conf['remote_users'], remote_passwords=conf['remote_passwords'], timeout=conf['timeout'],
        localhost_pass=conf['localhost_pass'], tail_lines=conf['tail_lines'], target_mail=conf['target_mail'],
        mail_user=conf['mail_user'], mail_password=conf['mail_password'], test_name=conf['test_name'],
        env_state_uri=conf['env_state_uri'], env_state_pass=conf['env_state_pass']
    )

    manager_obj._rhv_manager()


