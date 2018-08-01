import logging, os, datetime, socket, sys, tarfile, gzip
from traceback import print_stack
import argparse
from rrmngmnt.host import Host

LOCALHOST_LOGS_PATH = os.path.expanduser("~/tmp")
EXTRACTED_FOLDER_NAME = 'extracted'
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
    def __init__(self, time_start, path_logs):
        self.time_start = time_start[:-3]  # cutting seconds. '2018-07-16 03:39:04 --> '2018-07-16 03:39'
        self.path_logs = path_logs


    def parse_logs(self):
        logger.info('Starting to parse files in ' + self.path_logs)
        events_lst = []
        TIME_START_FOUND = False  # boolean. false by default. meaning that the program is in mode of searching for 1st
        # time_start occurrence. when it becomes true, we switch to mode of searching for events and gathering them.

        if not os.path.isdir(self.path_logs):
            logger.error("path_logs is not a valid directory on local machine: " + self.path_logs)
            sys.exit()

        all_files = os.listdir(self.path_logs)
        engine_log_files = [x for x in all_files if 'engine' in x]
        engine_log_files.sort(reverse=True)  # now engine logs are sorted in DESC order. older is first. engine.log is last

        for file_to_parse in engine_log_files:
            full_file_name = os.path.join(self.path_logs, file_to_parse)
            logger.info("Parsing " + file_to_parse)
            if file_to_parse.endswith('.gz'):
                full_file_name = self.extract_gz_file(full_file_name)

                # continue to next file if extraction of gz failed in 'extract' for some reason
                if full_file_name is None:
                    continue

            try:
                with open(full_file_name) as f:
                    for line in f:
                        if self.time_start in line and not TIME_START_FOUND:
                            logger.info("Found start time: %s in: %s" % (self.time_start, os.path.basename(full_file_name)))
                            TIME_START_FOUND = True

                        if TIME_START_FOUND:
                            if 'EVENT_ID:' in line:
                                logger.debug('Found string "EVENT_ID" line. appending it to "events_lst". '
                                             'File: %s The line: %s' % (full_file_name, line))
                                events_lst.append(line)

            except IOError:
                logger.error("File does not appear to exist" + full_file_name)

        logger.info('Finished parsing logs')



    def extract_gz_file(self, full_file_name):
        # logger.info("Attempting to extract " + full_file_name)
        full_folder_path_for_extracted_file = os.path.join(self.path_logs, EXTRACTED_FOLDER_NAME)  # e.g /some/dir/extracted
        if not os.path.exists(full_folder_path_for_extracted_file):
            logger.info("Extraction folder does not exist. attempting to create it. %s" % full_folder_path_for_extracted_file)
            os.makedirs(full_folder_path_for_extracted_file)
        gz_file_name = os.path.basename(full_file_name)  # e.g engine.log-20180718.gz
        full_file_path_for_extracted_file = os.path.join(full_folder_path_for_extracted_file,
                                                         gz_file_name.strip('.gz'))  # e.g /x/y/extracted/engine.log-20180718

        logger.info("Attempting to extract file %s to: %s" % (gz_file_name, full_file_path_for_extracted_file))
        try:
            os.system('gunzip -c %s > %s' %(full_file_name, full_file_path_for_extracted_file))
        except:
            logger.error("Failed to extract file %s to path %s \n will continue to next file"
                         % (full_file_name, full_file_path_for_extracted_file))
            print_stack()
            return None

        return full_file_path_for_extracted_file



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
    parser = argparse.ArgumentParser(description='This functionality parses engine events')
    parser.add_argument("-t", "--time_start", action="store", dest="time_start",
                        help="Start time of the listener. Used for parsing the events starting from that time."
                             "The valuse has to be string in format: "
                             "datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')"
                             "For example: '2018-07-19 10:25:17'", required=True)

    parser.add_argument("-p", "--path_logs", action="store", dest="path_logs",
                        help="Full LOCAL folder path of logs that need to be parsed.", required=True)

    args = parser.parse_args()
    # check start_time format
    try:
        datetime.datetime.strptime(args.time_start, '%Y-%m-%d %H:%M:%S')
    except:
        parser.error("Argument -t must be in the following format: '%Y-%m-%d %H:%M:%S'")

    scenario_finder = ScenarioFinder(time_start=args.time_start, path_logs=args.path_logs)
    scenario_finder.parse_logs()

if __name__ == '__main__':
    # Run as a script directly from terminal
    main()
