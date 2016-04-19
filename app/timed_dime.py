import queue
import random
import datetime
import time

import lib.synth
import lib.msg_proc
import lib.helper
import lib.interface


class TimedDime(lib.interface.Dime):

    MAX_WAIT_TIME_S = 8
    MIN_WAIT_TIME_S = 4

    def __init__(self, msg_proc, text_file_name, event_queue_size=4):
        super(TimedDime, self).__init__(msg_proc=msg_proc, event_queue_size=event_queue_size)

        self._text_file_name = text_file_name

    def run(self):
        self._logger.info("running, waiting on event queue...")
        lines = lib.helper.get_lines_from_file(self._text_file_name)
        if not lines:
            self._logger.error("got no lines from file '%s'", self._text_file_name)
            return

        offset_s = random.randint(self.MIN_WAIT_TIME_S, self.MAX_WAIT_TIME_S)
        trigger_time = datetime.datetime.now() + datetime.timedelta(0, offset_s)
        self._logger.info("reschedule now, trigger next event in ~%ds", offset_s)
        while not self.stopped():
            if trigger_time < datetime.datetime.now():
                offset_s = random.randint(self.MIN_WAIT_TIME_S, self.MAX_WAIT_TIME_S)
                trigger_time = datetime.datetime.now() + datetime.timedelta(0, offset_s)

                text_to_say = random.choice(lines)
                for target_queue in self._target_txt_queue_list:
                    try:
                        target_queue.put(text_to_say)
                    except queue.Full as exception:
                        self._logger.error("drop message '%s': %s", text_to_say, exception)

                self._logger.info("reschedule now, trigger next event in ~%ds", offset_s)
            else:
                self._logger.debug("trigger next event in %s seconds", (trigger_time - datetime.datetime.now()).seconds)
                time.sleep(1)

        self._logger.info("exit gracefully")


class TimedDimeRunner(lib.interface.DimeRunner):
    def __init__(self, cfg):
        super(TimedDimeRunner, self).__init__()

        self._xmpp_dime_config = cfg
        self._speech = None
        self._cam_dime = None

    def start(self):
        obj_name = self._xmpp_dime_config["dime"]["synthesizer"]
        synth_type = lib.helper.get_obj_type(obj_name)
        obj_name = self._xmpp_dime_config["dime"]["msg_proc"]
        msg_proc = lib.helper.get_obj_type(obj_name)

        self._speech = lib.synth.Speech(msg_queue_size=5, synthesizer=synth_type)
        self._cam_dime = TimedDime(msg_proc=msg_proc,
                                   text_file_name="data/chuck_norris_facts.txt",
                                   event_queue_size=2)

        if not self._speech.check_system():
            raise Exception("synthesizer not ready, exit immediately")
        if not self._cam_dime.check_system():
            raise Exception("dime not ready, exit immediately")

        # register synth message queue at dime
        self._cam_dime.register_target_txt_queue(self._speech.text_queue)

        self._cam_dime.start()
        self._speech.start()

        self._speech.text_queue.put("system successfully started - ready for take off!")

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
    lib.helper.kickstart(TimedDimeRunner)