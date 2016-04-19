# pylint: disable=line-too-long

import logging
import random


class TxtPassthrough(object):
    def __init__(self):
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self._logger.info("using text filter '%s'", self)

    def process(self, msg):
        text = self._process(msg)
        self._logger.debug("text before processor: '%s', text after processor: '%s'", msg, text)
        return text

    @staticmethod
    def _process(msg):
        return msg

    def __repr__(self):
        return self.__class__.__name__

    def __str__(self):
        return self.__repr__()


class XmppMsgPassthrough(object):
    def __init__(self):
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self._logger.info("using XMPP message filter '%s'", self)

    def process(self, msg):
        text = self._process(msg)
        self._logger.debug("text before processor: '%s', text after processor: '%s'", msg["body"], text)
        return text

    @staticmethod
    def _process(msg):
        return msg["body"]

    def __repr__(self):
        return self.__class__.__name__

    def __str__(self):
        return self.__repr__()


class XmppMsgBadWordRefuser(XmppMsgPassthrough):
    def __init__(self):
        super(XmppMsgBadWordRefuser, self).__init__()

        # source https://en.wikipedia.org/wiki/Seven_dirty_words
        self._seven_dirty_words = ("shit", "piss", "fuck", "cunt", "cocksucker", "motherfucker", "tits")

    def _process(self, msg):
        text = msg["body"]
        if any(bad_word in text for bad_word in self._seven_dirty_words):
            user = repr(msg['from']).split('@')[0]
            text = "%s wanted me to say bad words! i can not do that!" % user

        return text


class XmppMsgBadWordReplacer(XmppMsgBadWordRefuser):
    def __init__(self):
        super(XmppMsgBadWordReplacer, self).__init__()

    def _process(self, msg):
        text = msg["body"]
        bad_words_found = set([word for word in self._seven_dirty_words if word in text])
        text = []
        # remove all words which contain something from the 'bad word list'
        for word in text.split(' '):
            for bad_word in bad_words_found:
                if bad_word in word:
                    word = " 'bad word!' "
            text.append(word)
        clean_text = " ".join(text)

        return clean_text


class XmppMsgBadWordBlaming(XmppMsgBadWordRefuser):
    def __init__(self):
        super(XmppMsgBadWordBlaming, self).__init__()

    def _process(self, msg):
        text = msg["body"]

        bad_word_list = []
        for bad_word in self._seven_dirty_words:
            if bad_word in text:
                bad_word_list.append(bad_word)

        bad_words_found = list(set(bad_word_list))
        if len(bad_words_found):
            multiple = ""
            if len(bad_words_found) > 1:
                multiple = "words like "

            bad_word_string = self._get_text_enumeration(bad_words_found)
            user = repr(msg['from']).split('@')[0]

            extra = "such a naughty guy!" if bool(random.getrandbits(1)) else "i can not believe that!"
            text = "oh no! %s wanted me to say %s %s, %s" % (user, multiple, bad_word_string, extra)

        return text

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
