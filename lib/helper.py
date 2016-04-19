# pylint: disable=line-too-long

import time
import logging
import argparse
import sys
import json
import queue

import lib.synth
import lib.interface
import lib.msg_proc


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)-12s %(levelname)-8s %(name)-16s %(message)s')
LOGGER = logging.getLogger(__name__)


class Dime(lib.interface.StoppableThread):
    def __init__(self, msg_proc, event_queue_size=4):
        super(Dime, self).__init__()
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self._msg_proc = msg_proc()
        self._event_queue = queue.Queue(maxsize=event_queue_size)
        self._target_txt_queue_list = []

    @property
    def event_queue(self):
        return self._event_queue

    def check_system(self):
        self._logger.warning("dummy implementation")
        return True

    def run(self):
        self._logger.info("running, waiting on event queue...")
        while not self.stopped():
            try:
                queue_element = self.event_queue.get(timeout=1)
            except queue.Empty:
                self._logger.debug("timeout on empty queue, continue")
                continue

            text_to_say = self._msg_proc.process(queue_element)
            for target_queue in self._target_txt_queue_list:
                try:
                    target_queue.put(text_to_say)
                except queue.Full as exception:
                    self._logger.error("drop message '%s': %s", text_to_say, exception)

        self._logger.info("exit gracefully")

    def register_target_txt_queue(self, txt_queue):
        self._target_txt_queue_list.append(txt_queue)


def kickstart(dime_runner):
    LOGGER.info("starting application")

    parser = argparse.ArgumentParser(description='start dime application')
    parser.add_argument('--config', help='define a JSON config file')
    args = parser.parse_args()

    if not args.config:
        parser.print_help()
        sys.exit(1)

    with open(args.config, 'r') as cfg_file:
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


def get_obj_type(obj_name):
    try:
        obj_type = eval(obj_name)
    except Exception as exception:
        LOGGER.fatal("unable to create object from '%s': %s", obj_name, exception)
        raise exception

    return obj_type
