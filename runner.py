import argparse

from manager.manager import run_rhv_manager

parser = argparse.ArgumentParser(description='Bug hunter runner')
parser.add_argument("-p", "--runner_yaml_path", action="store", dest="runner_yaml_path",
                    help="Full local runner.yaml path", required=True)
args = parser.parse_args()


run_rhv_manager(args.runner_yaml_path)
