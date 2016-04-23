# pylint: disable=line-too-long

import logging
import random


class Passthrough(object):
    def __init__(self):
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self._logger.info("using XMPP message filter '%s'", self)

    def process(self, txt):
        text = self._process(txt)
        self._logger.debug("text before processor: '%s', text after processor: '%s'", txt, text)
        return text

    def _process(self, txt):
        return txt

    def __repr__(self):
        return self.__class__.__name__

    def __str__(self):
        return self.__repr__()


class BadWordRefuser(Passthrough):
    def __init__(self, user_name=None):
        super(BadWordRefuser, self).__init__()
        self._user_name = user_name if user_name else "they "

        # source https://en.wikipedia.org/wiki/Seven_dirty_words
        self._seven_dirty_words = ("shit", "piss", "fuck", "cunt", "cocksucker", "motherfucker", "tits")

    def _process(self, txt):
        txt = txt.lower()
        if not any(bad_word in txt for bad_word in self._seven_dirty_words):
            return txt

        return "%s wanted me to say bad words! i can not do that!" % self._user_name


class BadWordReplacer(BadWordRefuser):
    def __init__(self):
        super(BadWordReplacer, self).__init__()

    def _process(self, txt):
        txt = txt.lower()
        bad_words_found = set([word for word in self._seven_dirty_words if word in txt])
        # remove all words which contain something from the 'bad word list'
        new_txt = []
        for word in txt.split(' '):
            for bad_word in bad_words_found:
                if bad_word in word:
                    word = " 'bad word!' "
            new_txt.append(word)
        clean_txt = " ".join(new_txt)

        return clean_txt


class BadWordBlaming(BadWordRefuser):
    def __init__(self):
        super(BadWordBlaming, self).__init__()

    def _process(self, txt):
        txt = txt.lower()
        bad_word_list = []
        for bad_word in self._seven_dirty_words:
            if bad_word in txt:
                bad_word_list.append(bad_word)

        bad_words_found = list(set(bad_word_list))
        if not len(bad_words_found):
            return txt

        multiple = ""
        if len(bad_words_found) > 1:
            multiple = "words like "

        bad_word_string = self._get_text_enumeration(bad_words_found)

        extra = "that's incredible!" if bool(random.getrandbits(1)) else "i can not believe that!"
        return "oh no! %s wanted me to say %s %s, %s" % (self._user_name, multiple, bad_word_string, extra)

    @staticmethod
    def _get_text_enumeration(word_list):
        if len(word_list) == 1:
            return word_list[0]

        ending = word_list[-2] + " and " + word_list[-1]

        text_enum = ""
        for word in word_list[:-2]:
            text_enum = text_enum + word + ", "

        text_enum = text_enum.strip(',')
        text_enum = text_enum + ending

        return text_enum


class ReverseWords(Passthrough):
    def __init__(self):
        super(ReverseWords, self).__init__()

    def _process(self, txt):
        result = ""
        for word in txt.split(' '):
            result = result + " " + word[::-1]
        return result
