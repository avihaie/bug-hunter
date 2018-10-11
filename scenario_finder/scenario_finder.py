import logging, os, datetime, sys, argparse
from traceback import print_stack
from datetime import datetime, timedelta
import config

EXTRACTED_FOLDER_NAME = 'extracted_gz'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
MINUTES_INTERVAL = 5

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - ''%(message)s',
    datefmt=DATETIME_FORMAT)
logger = logging.getLogger(__name__)


class ScenarioFinder:
    """
    Class for searching and storing the needed events from engine logs. can handle gz files as well as plain text files.
    """

    def __init__(self, time_start, path_logs, event_string, scenario_result_file_path):
        self.time_start = time_start
        self.path_logs = path_logs
        self.event_string_to_find = event_string
        self.events_found_lst = []  # stores the lines of logs where  event_string_to_find was found
        self.time_start_found = False  # it becomes true when 'time_start' string is found inside parsed logs
        self.scenario_result_file_path = scenario_result_file_path

    def parse_logs(self):
        """
        Main method where all of parsing logic's begins. It calls other methods for different tasks.
        """
        logger.info('Starting to parse files in ' + self.path_logs)
        logger.info('******* Event sting is: %s', self.event_string_to_find)
        logger.info('******* Time as input is :%s', self.time_start)

        self.check_log_dir_exists(self.path_logs)

        all_log_files_lst = os.listdir(self.path_logs)
        engine_log_files_lst = [x for x in all_log_files_lst if 'engine' in x]
        engine_log_files_lst.sort(reverse=False)  # now engine logs are sorted in DESC order. engine.log is first, then
                                                  # the oldest file, and last index will be the most recent.
        engine_log_files_lst.insert(len(engine_log_files_lst), engine_log_files_lst.pop(0))  # moving [0] element (engine.log)
                                                                                             # TO last place index

        for file_to_parse in engine_log_files_lst:
            full_file_name = os.path.join(self.path_logs, file_to_parse)
            logger.info("About to parse: " + file_to_parse)
            if file_to_parse.endswith('.gz'):
                full_file_name = self.extract_gz_file(full_file_name)

                # continue to next file if extraction of gz failed in 'extract' for some reason
                if full_file_name is None:
                    continue

            try:
                with open(full_file_name) as f:
                    for line in f:
                        if not self.time_start_found:
                            self.time_start_found = self.find_time_start_string_in_line(line, full_file_name)

                        if self.time_start_found:
                            self.find_event_string_in_line(full_file_name, line)

            except IOError as e:
                logger.error("File does not appear to exist: %s\n %s" % (full_file_name, e))

        logger.info('Finished parsing logs, about to dump the scenario to: ' + self.scenario_result_file_path)
        self.dump_scenario_list_to_file()

    def dump_scenario_list_to_file(self):
        """
        Writes the list of found event lines (which were extracted from logs) to a txt file.
        """
        try:
            with open(self.scenario_result_file_path, 'w') as f:
                f.writelines(self.events_found_lst)
                logger.info("Wrote scenario events to file: " + self.scenario_result_file_path)
        except IOError as e:
            logger.error("Failed to dump scenarios list to file: %s \n %s" % (self.scenario_result_file_path, e))

    def find_event_string_in_line(self, full_file_name, line):
        """
        Finds the events string inside a line from some log file, and puts it to a list.
        :param full_file_name: Full path to a plain text file (could be extracted GZ). used only for logging here.
        :param line: Line from a file which needs to be parsed for the events string.
        """
        if self.event_string_to_find in line:
            logger.debug('Found string: %s inside line. appending it to events_found_lst. File: %s The line: %s'
                         % (self.event_string_to_find, full_file_name, line))
            self.events_found_lst.append(line)

    def find_time_start_string_in_line(self, line, full_file_name):
        """
        Finds the start time string inside a line from a log file. Returns true if found, false if not found.
        :param line: Line from a file which needs to be parsed for the time string.
        :param full_file_name: full_file_name: Full path to a plain text file (could be extracted GZ).
        Used only for logging here.
        :return:  true if found, false if not found.
        """
        datetime_object_start_time = datetime.strptime(self.time_start, DATETIME_FORMAT)
        try:
            datetime_str_in_line = line.split(',')[0]
            datetime_object_in_line = datetime.strptime(datetime_str_in_line, DATETIME_FORMAT)

            # True if timestamp in line is between start time and start time + min
            # example: '2018-07-25 03:11:35' <= '2018-07-25 03:15:35' <= '2018-07-25 03:16:35'
            if datetime_object_start_time <= datetime_object_in_line <= \
                    datetime_object_start_time + timedelta(minutes=MINUTES_INTERVAL):
                logger.info("Found start time string: %s in file: %s Beginning to search for event string: %s"
                            % (self.time_start, os.path.basename(full_file_name), self.event_string_to_find))
                return True
            return False

        except:
            return False

    def check_log_dir_exists(self, dir_path):
        """
        Checks logs dir for existence. Log dir is a directory for holding all of the log files for parsing.
        Exits the program if the directory does not exist.
        :param dir_path: Full path of the directory.
        """
        #  checking existence of logs directory which we will parse
        if not os.path.isdir(dir_path):
            logger.error("Not a valid directory on local machine: " + dir_path)
            sys.exit()

    def extract_gz_file(self, full_file_name):
        """
        Extracts a gz file to folder name as defined in 'EXTRACTED_FOLDER_NAME' inside the folder where the logs reside.
        For example: '/home/ilan/tmp/bughunter/extracted_gz/'
        :param full_file_name: Full path to a GZ file.
        :return: Full path to the extracted file inside 'extracted' folder.
        """
        full_folder_path_for_extracted_file = os.path.join(self.path_logs,
                                                           EXTRACTED_FOLDER_NAME)  # e.g /some/dir/extracted

        if not os.path.exists(full_folder_path_for_extracted_file):
            logger.info(
                "Extraction folder for gz files does not exist. attempting to create it. %s"
                % full_folder_path_for_extracted_file)
            os.makedirs(full_folder_path_for_extracted_file)

        gz_file_name = os.path.basename(full_file_name)  # e.g engine.log-20180718.gz
        full_file_path_for_extracted_file = os.path.join(
            full_folder_path_for_extracted_file, gz_file_name.strip('.gz'))  # e.g /x/y/extracted/engine.log-20180718

        logger.info("Attempting to extract file %s to: %s" % (gz_file_name, full_file_path_for_extracted_file))
        try:
            os.system('gunzip -c %s > %s' % (full_file_name, full_file_path_for_extracted_file))
        except Exception as e:
            logger.error("Failed to extract file %s to path %s\n will continue to next file\n %s"
                         % (full_file_name, full_file_path_for_extracted_file, e))
            print_stack()
            return None

        return full_file_path_for_extracted_file


def main():
    """
    In case of manual execution -

    e.g python scenario_finder.py -t "2018-07-25 03:08:41" -p "/home/ilan/tmp/bughunter" -e "EVENT_ID"

    Options -
        * -t, --time_start : Test start time. states starting from which time we should search for events. it must be in
                            the following format: '%Y-%m-%d %H:%M:%S'
        * -p, --path_logs : Full path of logs folder on local machine.
        * -e, --events_to_grab : String for which we need to search inside log files. When found, the line is stored
                                and written to output file. In Engine log this would be 'EVENT_ID'
        * -s, --scenario_result_file_path : Full path to a file in which we want to store the events list. By default
                                            It would be: config.LOCALHOST_LOGS_PATH/scenario_file_<date_time_now>.txt
                                            Where date time format is '%Y-%m-%d %H:%M:%S'.

    """
    datetime_now = datetime.datetime.now().strftime(DATETIME_FORMAT)

    parser = argparse.ArgumentParser(description='This functionality parses engine events')
    parser.add_argument("-t", "--time_start", action="store", dest="time_start",
                        help="Start time of the listener. Used for parsing the events starting from that time."
                             "The valuse has to be string in format: "
                             "datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')"
                             "For example: '2018-07-19 10:25:17'", required=True)

    parser.add_argument("-p", "--path_logs", action="store", dest="path_logs",
                        help="Full LOCAL folder path of logs that need to be parsed.", required=True)

    parser.add_argument("-e", "--events_to_grab", action="store", dest="event_string",
                        help="This is the string we are looking for, inside the logs", required=True)

    parser.add_argument("-s", "--scenario_result_file_path", action="store", help="Full path for a result file where we"
                        " wish to save the scenario event. This is optional arg. if not specified,"
                                                                                  " the path will be as default.",
                        dest="scenario_result_file_path", nargs="?",
                        const="%s/scenario_file_%s.txt" % (config.LOCALHOST_LOGS_PATH, datetime_now),
                        default="%s/scenario_file_%s.txt" % (config.LOCALHOST_LOGS_PATH, datetime_now))
    # const sets the default when there are 0 arguments. If you want to set -s to some value even if no -s is specified,
    # then include default=..  nargs=? means 0-or-1 arguments

    args = parser.parse_args()
    # check start_time format
    try:
        datetime.datetime.strptime(args.time_start, DATETIME_FORMAT)
    except:
        parser.error("Argument -t must be in the following format: " + DATETIME_FORMAT)

    scenario_finder = ScenarioFinder(time_start=args.time_start, path_logs=args.path_logs,
                                     event_string=args.event_string,
                                     scenario_result_file_path=args.scenario_result_file_path)
    scenario_finder.parse_logs()


if __name__ == '__main__':
    # Run as a script directly from terminal
    main()
