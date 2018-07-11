import smtplib
import logging
import argparse


class Notifier:
    """
    Notifier class, can notify both by sending an email or/and console of an event of the user choice
    """

    def logger_setup(self, logger_name):
        """Setup logger for both console and file"""
        logger = logging.getLogger(logger_name)
        logger_path = "/tmp/" + logger.name
        logger_format = '%(asctime)s %(name)s %(levelname)s %(lineno)d %(message)s'

        # set up logging to file
        logging.basicConfig(
            level=logging.INFO,
            format=logger_format,
            datefmt='%Y-%m-%d %H:%M:%S',
            filename=logger_path,
            filemode='w'
        )
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        # set a format which for console use
        formatter = logging.Formatter(logger_format)
        # tell the handler to use this format
        console.setFormatter(formatter)
        # add the handler to the root logger
        logging.getLogger('').addHandler(console)
        return logger

    def __init__(
        self, event, event_details, target_mail, mail_user, mail_pass, host_name, test_name
    ):
        self.logger = self.logger_setup("notifier.log")
        self.event = event
        self.event_details = event_details
        self.target_mail = target_mail
        self.mail_user = mail_user
        self.mail_pass = mail_pass
        self.host_name = host_name
        self.test_name = test_name
        self.logger.info(
            "Initiating notifier object with params: event: %s\ntarget mail: %s\nmail username: %s\nmail password: %s\n"
            "host name: %s\ntest name: %s" % (
                self.event, self.target_mail, self.mail_user, self.mail_pass, self.host_name, self.test_name
            )
        )

    def send_mail(self):
        """
        Send an email when an issue occurs to a chosen mail using gmail server
        An existing gmail account should exist in order to achieve this.
        """
        try:
            mail = smtplib.SMTP('smtp.gmail.com', 587)
            mail.ehlo()
            mail.starttls()
            mail.login(self.mail_user, self.mail_pass)
            content = "Subject: Test %s %s on host %s\n\n%s" % (
                self.test_name, self.event, self.host_name, self.event_details
            )
            mail.sendmail(self.mail_user, self.target_mail, content)
            mail.close()
        except Exception as e:
            self.logger.error("Sending mail failed with Error %s", e)

        else:
            self.logger.info("Mail sent to %s", self.target_mail)

    def notify_console(self):
        """Notify console about an event that occurred using the logger"""
        self.logger.error("Test %s Event %s OCCURRED on host %s!!!\nEvent %s\nMail sent to %s" % (
            self.test_name, self.event.capitalize(), self.host_name, self.event_details, self.target_mail
        ))

    def main(self):
        # Run from code - not directly from terminal
        self.notify_console()
        self.send_mail()


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
    parser = argparse.ArgumentParser(description='this function can be used '
                                                 'to notify after an event occured via mail and console')

    parser.add_argument("-e", "--event", action="store", dest="event",
                        help="summery of the event (e.g. -e 'Exception caught!')")

    parser.add_argument("-d", "--event_details", action="store", dest="event_details",
                        help="event details (e.g. -d 'NullPointerException ...')")

    parser.add_argument("-u", "--mail_user", action="store", dest="mail_user",
                        help="email user which is equal to email itself (e.g. -u test@gmail.com)")

    parser.add_argument("-p", "--mail_password", action="store", dest="mail_password",
                        help="email password (e.g. -p 123456)")

    parser.add_argument("-o", "--host_name", action="store", dest="host_name",
                        help="host name that the issue occured on (e.g. -o storage-ge4-test.scl.lab.tlv.redhat.com)")

    parser.add_argument("-t", "--test_name", action="store", dest="test_name",
                        help="name of the test (e.g. -e 'TestCase18145')")

    options = parser.parse_args()

    notify_ob = Notifier(options.event, options.event_details, options.mail_user,  options.mail_user,
                         options.mail_password, options.host_name, options.test_name)
    notify_ob.notify_console()
    notify_ob.send_mail()

if __name__ == '__main__':
    # Run as a script directly from terminal
    main()
