import threading
import time
import logging
import argparse
import sys
import json


LOGGER = logging.getLogger(__name__)


class StoppableThread(threading.Thread):
    """thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition.

    source: http://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread-in-python
    """
    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()


def kickstart(dime_runner):
    LOGGER.info("starting application")

    parser = argparse.ArgumentParser(description='start dime application')
    parser.add_argument('--config', help='define a JSON config file')
    ARGS = parser.parse_args()

    if not ARGS.config:
        parser.print_help()
        sys.exit(1)

    with open(ARGS.config, 'r') as cfg_file:
        cfg = json.load(cfg_file)

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
