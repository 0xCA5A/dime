import logging
import tempfile

import lib.interface


class Festival(lib.interface.TtsSynth):
    BINARY_NAME = "festival"

    def __init__(self):
        super(Festival, self).__init__()

    def say(self, text):
        language = "english"
        command_string = 'echo "%s" | %s --tts ' \
                         '--language %s' % (text, self.BINARY_NAME, language)
        if self.system_call(command_string) == 0:
            return True

    def check_system(self):
        return self.is_binary_here(self.BINARY_NAME)


class Espeak(lib.interface.TtsSynth):
    BINARY_NAME = "espeak"

    def __init__(self):
        super(Espeak, self).__init__()

    def say(self, text):
        command_string = '%s --stdout "%s" | aplay' % (self.BINARY_NAME, text)
        if self.system_call(command_string) == 0:
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

        if self.system_call(command_string) == 0:
            return True

    def check_system(self):
        return self.is_binary_here(self.BINARY_NAME) and self.is_binary_here("aplay")


class Dummy(lib.interface.TtsSynth):
    def __init__(self):
        super(Dummy, self).__init__()

    def say(self, text):
        command_string = 'echo "say: %s"' % text
        if self.system_call(command_string) == 0:
            return True

    def check_system(self):
        return True


class Speech(object):

    def __init__(self, synthesizer=Pico2Wave):
        super(Speech, self).__init__()
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        # TODO: do this more controlled, avoid exceptions in constructor
        self._synthesizer = synthesizer()
        self.logger.debug("configure '%s' as "
                          "synthesizer", self._synthesizer.__class__.__name__)

    def __repr__(self):
        return self._synthesizer.__class__.__name__

    def __str__(self):
        return self.__repr__()

    def say(self, text):
        return self._synthesizer.say(text)

    def check_system(self):
        return self._synthesizer.check_system()
