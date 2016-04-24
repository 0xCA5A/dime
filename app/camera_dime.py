import lib.synth
import lib.msg_proc
import lib.helper
import lib.interface


class CameraDime(lib.interface.Dime):
    def __init__(self, msg_proc, event_queue_size=4):
        super(CameraDime, self).__init__(msg_proc=msg_proc, event_queue_size=event_queue_size)


class CameraDimeRunner(lib.interface.DimeRunner):
    def __init__(self, cfg):
        super(CameraDimeRunner, self).__init__()

        self._xmpp_dime_config = cfg
        self._speech = None
        self._dime = None

    def start(self):
        obj_name = self._xmpp_dime_config["dime"]["synthesizer"]
        synth_type = lib.helper.get_obj_type(obj_name)
        obj_name = self._xmpp_dime_config["dime"]["msg_proc"]
        msg_proc = lib.helper.get_obj_type(obj_name)

        self._speech = lib.synth.Speech(msg_queue_size=5, synthesizer=synth_type)
        self._dime = CameraDime(event_queue_size=2, msg_proc=msg_proc)

        if not self._speech.check_system():
            raise Exception("synthesizer not ready, exit immediately")
        if not self._dime.check_system():
            raise Exception("dime not ready, exit immediately")

        # register synth message queue at dime
        self._dime.register_target_txt_queue(self._speech.text_queue)

        self._dime.start()
        self._speech.start()

        self._speech.text_queue.put("system successfully started - ready for take off!")

    def stop(self):
        if self._dime:
            self._dime.stop()
            self._dime.join()
        if self._speech:
            self._speech.stop()
            self._speech.join()

    def is_up_and_running(self):
        system_status = True
        if self._dime and not self._dime.is_alive():
            self._logger.error("%s thread ist dead", self._dime)
            system_status = False
        if self._speech and not self._speech.is_alive():
            self._logger.error("%s thread ist dead", self._speech)
            system_status = False

        return system_status


if __name__ == "__main__":
    lib.helper.kickstart(CameraDimeRunner)