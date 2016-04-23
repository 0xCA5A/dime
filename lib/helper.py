# pylint: disable=line-too-long

import time
import logging
import argparse
import sys
import subprocess
import json

import lib.synth
import lib.msg_proc


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)-12s %(lineno)-4s %(levelname)-8s %(name)-16s %(message)s')
LOGGER = logging.getLogger(__name__)


def kickstart(dime_runner):
    LOGGER.info("starting application")

    parser = argparse.ArgumentParser(description='start dime application')
    parser.add_argument('--config', help='define a JSON config file')
    args = parser.parse_args()

    if not args.config:
        parser.print_help()
        sys.exit(1)

    try:
        with open(args.config, 'r') as cfg_file:
            cfg = json.load(cfg_file)
    except Exception as exception:
        LOGGER.error("unable to import JSON configuration: %s", exception)
        sys.exit(1)

    dime_runner = dime_runner(cfg)
    try:
        dime_runner.start()
    except Exception as exception:
        LOGGER.error(exception)
        sys.exit(1)

    while True:
        try:
            LOGGER.debug("in main idle loop")
            if not dime_runner.is_up_and_running():
                break

            time.sleep(1)

        except KeyboardInterrupt:
            LOGGER.info("KeyboardInterrupt caught, shut application down")
            break

    dime_runner.stop()
    LOGGER.info("exit gracefully")


def get_obj_type(obj_name):
    try:
        obj_type = eval(obj_name)
    except Exception as exception:
        LOGGER.fatal("unable to create object from '%s': %s", obj_name, exception)
        raise exception

    return obj_type


def get_lines_from_file(file_name):
    with open(file_name) as text_file:
        content = [line.strip() for line in text_file.readlines()]

    # filter comment lines #
    content = [line for line in content if not line.startswith("#")]

    ascii_content = []
    for line in content:
        ascii_line= str(line.encode('utf-8').decode('ascii', 'ignore'))
        ascii_content.append(ascii_line)

    LOGGER.debug("read %d lines from file '%s'", len(ascii_content), file_name)
    return ascii_content


def system_call(command):
    LOGGER.info("fire up system call '%s'", command)
    ascii_command = str(command.encode('utf-8').decode('ascii', 'ignore'))
    task = subprocess.Popen(ascii_command, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return task.wait()
