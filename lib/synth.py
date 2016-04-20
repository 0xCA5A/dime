# pylint: disable=line-too-long
import logging
import tempfile
import queue

import lib.interface
import lib.helper


class Festival(lib.interface.TtsSynth):
    BINARY_NAME = "festival"

    def __init__(self):
        super(Festival, self).__init__()

    def say(self, text):
        command_string = 'echo "%s" | %s --tts' % (text, self.BINARY_NAME)
        if lib.helper.system_call(command_string) == 0:
            return True

    def check_system(self):
        return self.is_binary_here(self.BINARY_NAME)


class Espeak(lib.interface.TtsSynth):
    BINARY_NAME = "espeak"

    def __init__(self):
        super(Espeak, self).__init__()

    def say(self, text):
        command_string = '%s --stdout "%s" | aplay' % (self.BINARY_NAME, text)
        if lib.helper.system_call(command_string) == 0:
            return True

    def check_system(self):
        return self.is_binary_here(self.BINARY_NAME) and self.is_binary_here("aplay")


class Pico2Wave(lib.interface.TtsSynth):
    BINARY_NAME = "pico2wave"

    def __init__(self):
        super(Pico2Wave, self).__init__()

    def say(self, text):
        languages = ('en-US', 'en-GB', 'de-DE', 'es-ES', 'fr-FR', 'it-IT')
        lang = languages[0]
        tmp_file_name = tempfile.NamedTemporaryFile(prefix="pico_2_wave_",
                                                    suffix=".wav",
                                                    delete=False).name
        command_string = '%s --lang %s --wave %s "%s" ; aplay %s' % (self.BINARY_NAME,
                                                                     lang,
                                                                     tmp_file_name,
                                                                     text,
                                                                     tmp_file_name)
        if lib.helper.system_call(command_string) == 0:
            return True

    def check_system(self):
        return self.is_binary_here(self.BINARY_NAME) and self.is_binary_here("aplay")


class Dummy(lib.interface.TtsSynth):
    def __init__(self):
        super(Dummy, self).__init__()

    def say(self, text):
        command_string = 'echo "%s"' % text
        if lib.helper.system_call(command_string) == 0:
            return True

    def check_system(self):
        return True


class Speech(lib.interface.StoppableThread):

    def __init__(self, msg_queue_size=5, synthesizer=Pico2Wave):
        super(Speech, self).__init__()
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self._text_queue = queue.Queue(maxsize=msg_queue_size)

        # TODO: do this more controlled, avoid exceptions in constructor
        self._synthesizer = synthesizer()
        self._logger.debug("configure '%s' as "
                           "synthesizer", self._synthesizer.__class__.__name__)

    @property
    def text_queue(self):
        return self._text_queue

    def __repr__(self):
        return self._synthesizer.__class__.__name__

    def __str__(self):
        return self.__repr__()

    def check_system(self):
        return self._synthesizer.check_system()

    def run(self):
        self._logger.info("running, waiting on event queue...")
        while not self.stopped():
            try:
                queue_element = self.text_queue.get(timeout=1)
            except queue.Empty:
                self._logger.debug("timeout on empty queue, continue")
                continue

            if not self._synthesizer.say(queue_element):
                self._logger.error("could not say '%s' using synthesizer"
                                   " '%s'!", queue_element, self._synthesizer)

        self._logger.info("exit gracefully")
