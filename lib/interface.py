# pylint: disable=line-too-long

import logging
import os
import threading


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
        if self.system_call(command_string) == 0:
            return True

        self.logger.error("binary not found on your system")

    def system_call(self, command):
        self.logger.debug("fire up system call '%s'", command)

        ascii_command = str(command.encode('utf-8').decode('ascii', 'ignore'))
        return os.system(ascii_command)
