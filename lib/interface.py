# pylint: disable=line-too-long

import logging
import queue
import threading

import lib.helper


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


class DimeRunner(object):
    def __init__(self):
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    def start(self):
        self._log_default_impl()

    def is_up_and_running(self):
        self._log_default_impl()

    def _log_default_impl(self):
        self._logger.warning("abstract function called")


class Speech(object):
    def __init__(self):
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    def say(self, text):
        self._log_impl_error()
        return False

    def check_system(self):
        self._log_impl_error()

    def _log_impl_error(self):
        self.logger.warning("template function called")


class TtsSynth(Speech):
    def __init__(self):
        super(TtsSynth, self).__init__()

    def is_binary_here(self, binary_name):
        self.logger.debug("check for binary '%s' on system", binary_name)
        command_string = "which %s" % binary_name
        if lib.helper.system_call(command_string) == 0:
            return True

        self.logger.error("binary not found on your system")


class Dime(StoppableThread):
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
