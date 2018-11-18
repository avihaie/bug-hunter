import argparse

from manager.manager import run_rhv_manager

parser = argparse.ArgumentParser(description='Bug hunter runner')
parser.add_argument(
    "-p", "--runner_yaml_path", action="store", dest="runner_yaml_path", type=str, help="Full local runner.yaml path, for example: /tmp/runner.yaml",
    required=True
)
options = parser.parse_args()

if options.runner_yaml_path:
    runner_yaml_path = options.runner_yaml_path
else:
    raise RuntimeError("Missing arguments! usage : %s", parser.parse_args(['-h']))

run_rhv_manager(runner_yaml_path)

