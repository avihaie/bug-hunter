Main functionality:
Dumps selected logs(+ logs short version) from selected remote hosts and collect them to a single localhost directory.

Can used as a library used as part of the bug-hunter application or as a stand alone application .

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
    * -m, --machine :followed by ip,username & password & the required log/s of the remote
      machines (e.g. -m 10.0.0.0 root P@SSW0RD /var/log/vdsm1.log /var/log/vdsm2.log)
      each machine should be preceded by -m separately
    * -l,--linesnumber:  option that is followed by the integer value
      of the lines taken from the end of the selected log file
      (e.g. -f /log/vdsm/vdsm.log -l 1000)  for getting the short version of that log (default is 1000 last lines)
    * -p,--localhostpass:  option that followed by the string value of
      the root password of the localhost.
      (e.g. -p "password")

Example for manual usage:
python log_dumper/log_dumper.py -m 10.0.0.1 root password /var/log/vdsm/vdsm.log /var/log/vdsm/vdsm2.log -m 10.0.0.2 root password /var/log/vdsm/vdsm3.log -l 1000 -p "1234"

This will dump logs
from:
 remote host 10.0.0.1 , logs /var/log/vdsm/vdsm.log + /var/log/vdsm/vdsm2.log
 remote host 10.0.0.2 , log /var/log/vdsm/vdsm3.log
 
To:
locahost which is where the application runs at /tmp/<timestamp>
