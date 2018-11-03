import logging
import os

# set up logging to file
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - '
           '%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class bugzilla_report_maker:
    """
    Generate a bugzilla report template
    """

    def __init__(self, logs_path, issue_found, test_name, components_versions, events_file_path):
        self.logs_path = logs_path
        self.issue_found = issue_found
        self.test_name = test_name
        self.components_versions = components_versions
        self.events_file_path = events_file_path

    def tail_lines_event_log(self, lines=10):
        stdin, stdout = os.popen2("tail -n " + str(lines) + " " + self.events_file_path)
        stdin.close()
        list_of_lines = stdout.readlines()
        stdout.close()
        lines_in_string = "".join([" ".join(tup) for list in list_of_lines for tup in list])

        return lines_in_string

    def create_bugzilla_file(self):
        """
        Create a bugzilla report file
        """
        data_dict = {}
        data_dict["description_of_problem"] = "Runnning " + self.test_name + " caused:\n" + self.issue_found
        data_dict["version"] = self.components_versions
        data_dict["how_reporoduceble"] = ""
        data_dict["steps_to_reproduce"] = self.tail_lines_event_log()
        data_dict["actual results"] = self.issue_found
        data_dict["expected results"] = "This should not appear: %s" % self.issue_found
        data_dict["additional_info"] = "Logs full path:\n" + self.logs_path

        file_full_path = self.logs_path + "/" + "bugzilla_report"
        logger.info("Creating bugzilla report file %s" % file_full_path)

        try:
            with open(file_full_path, "w") as f:
                f.write("Description of problem:\n")
                f.write(data_dict["description_of_problem"] + "\n")
                f.write("\nVersion-Release number of selected component (if applicable):\n")
                f.write(str(data_dict["version"]) + "\n")
                f.write("\nHow reproducible:\n")
                f.write(data_dict["how_reporoduceble"])
                f.write("\nSteps to Reproduce:\n")
                f.write(data_dict["steps_to_reproduce"] + "\n")
                f.write("Actual results:\n")
                f.write(data_dict["actual results"] + "\n")
                f.write("\nExpected results:\n")
                f.write(data_dict["expected results"] + "\n")
                f.write("\nAdditional info:\n")
                f.write(data_dict["additional_info"] + "\n")
        except IOError as e:
            raise IOError("Writing to %s failed with error %s" % (file_full_path, e))







