import logging
import queue

import lib.synth
import lib.msg_filter
import lib.helper
import lib.interface


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)-12s %(levelname)-8s %(name)-16s %(message)s')
LOGGER = logging.getLogger(__name__)


class CameraDime(lib.helper.StoppableThread):

    def __init__(self, msg_proc, event_queue_size=4):
        super(CameraDime, self).__init__()
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self._msg_proc = msg_proc()
        self._event_queue = queue.Queue(maxsize=event_queue_size)
        self._target_queue_list = []

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
            for target_queue in self._target_queue_list:
                try:
                    target_queue.put(text_to_say)
                except queue.Full as exception:
                    self._logger.error("drop message '%s'", text_to_say, exception)

        self._logger.info("exit gracefully")


    def register_target_queue(self, queue):
        self._target_queue_list.append(queue)


class CameraDimeRunner(lib.interface.DimeRunner):
    def __init__(self, cfg):
        super(CameraDimeRunner, self).__init__()
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self._xmpp_dime_config = cfg

        self._speech = None
        self._cam_dime = None

    def start(self):
        try:
            synth_impl = eval(self._xmpp_dime_config["dime"]["synthesizer"])
        except Exception as exception:
            self._logger.fatal("unable to create object from '%s': %s", self._xmpp_dime_config["dime"]["synthesizer"], exception)
            return
        try:
            msg_proc = eval(self._xmpp_dime_config["dime"]["msg_filter"])
        except Exception as exception:
            self._logger.fatal("unable to create object from '%s': %s", self._xmpp_dime_config["dime"]["synthesizer"], exception)
            return

        self._speech = lib.synth.Speech(msg_queue_size=5, synthesizer=synth_impl)
        self._cam_dime = CameraDime(msg_proc=msg_proc, event_queue_size=2)

        if not self._speech.check_system():
            raise Exception("synthesizer not ready, exit immediately")
        if not self._cam_dime.check_system():
            raise Exception("dime not ready, exit immediately")

        # register synth message queue at dime
        self._cam_dime.register_target_queue(self._speech.text_queue)

        self._cam_dime.start()
        self._speech.start()

    def stop(self):
        if self._cam_dime:
            self._cam_dime.stop()
            self._cam_dime.join()
        if self._speech:
            self._speech.stop()
            self._speech.join()

    def is_up_and_running(self):
        system_status = True
        if self._cam_dime and not self._cam_dime.is_alive():
            self._logger.error("%s thread ist dead", self._cam_dime)
            system_status = False
        if self._speech and not self._speech.is_alive():
            self._logger.error("%s thread ist dead", self._speech)
            system_status = False

        return system_status


if __name__ == "__main__":
    lib.helper.kickstart(CameraDimeRunner)