import sys
import logging
import time
import queue
import copy
import json
import argparse

from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError, IqTimeout

import lib.synth
import lib.msg_filter
import lib.helper
import lib.interface


logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)-12s %(levelname)-8s %(name)-16s %(message)s')
LOGGER = logging.getLogger(__name__)


class MessageProxyXMPP(ClientXMPP):

    MAX_MESSAGE_SIZE = 256

    def __init__(self, jid, password, message_queue):
        super(MessageProxyXMPP, self).__init__(jid, password)
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self._message_queue = message_queue

        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)

    def session_start(self, event):
        self.send_presence()
        try:
            self.get_roster()
        except IqError as err:
            self._logger.error('there was an error getting the roster')
            self._logger.error(err.iq['error']['condition'])
            self.disconnect()
        except IqTimeout:
            self._logger.error('server is taking too long to respond')
            self.disconnect()

    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):

            if len(msg['body']) > self.MAX_MESSAGE_SIZE:
                msg.reply("received message is too long (%d chars, max: %d), "
                          "drop message" % (len(msg['body']), self.MAX_MESSAGE_SIZE)).send()
                return

            if self._message_queue.full():
                msg.reply("too many messages pending, drop message").send()
                return

            # FIXME: using copy here due to reuse of msg object for response
            msg_cpy = copy.copy(msg)
            self._message_queue.put(msg_cpy)

            msg.reply("process message '%s' " % (msg['body'].strip()).send()


class XmppDime(lib.helper.StoppableThread):
    def __init__(self, synthesizer, xmpp_msg_filter, event_queue_size=4):
        super(XmppDime, self).__init__(event_queue_size)
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self._speech = lib.synth.Speech(synthesizer=synthesizer)
        self._xmpp_msg_filter = xmpp_msg_filter()

    def check_system(self):
        return self._speech.check_system()

    def run(self):
        self._logger.info("running, waiting on event queue...")
        while not self.stopped():
            try:
                queue_element = self.event_queue.get(timeout=1)
            except queue.Empty:
                self._logger.debug("timeout on empty queue, continue")
                continue

            text_to_say = self._xmpp_msg_filter.get_text(queue_element)
            if not self._speech.say(text_to_say):
                self._logger.error("could not say '%s' using synthesizer"
                                   " '%s'!", text_to_say, self._speech)

        self._logger.info("exit gracefully")


class XmppDimeRunner(lib.interface.DimeRunner):
    def __init__(self, cfg):
        super(XmppDimeRunner, self).__init__()
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self._xmpp_dime_config = cfg
        synth_impl = eval(cfg["dime"]["synthesizer"])
        msg_f = eval(cfg["dime"]["msg_filter"])

        self._synth = synth_impl(msg_queue_size=5, synthesizer=synth_impl)
        self._xmpp_dime = XmppDime(xmpp_msg_filter=msg_f, synth_msg_queue=self._synth.msg_queue)


        self._xmpp_proxy = MessageProxyXMPP(self._xmpp_dime_config["xmpp"]["jid"],
                                            self._xmpp_dime_config["xmpp"]["pwd"],
                                            self._xmpp_dime.event_queue)

    def start(self):
        if not self._xmpp_dime.check_system():
            raise Exception("dime system not ready, exit immediately")
        self._xmpp_dime.start()
        self._xmpp_proxy.connect()
        self._xmpp_proxy.process(block=False)

    def stop(self):
        if self._xmpp_proxy:
            self._xmpp_proxy.abort()
        if self._xmpp_dime:
            self._xmpp_dime.stop()
            self._xmpp_dime.join()

    def is_up_and_running(self):
        system_status = True

        bad_state = "disconnected"
        if self._xmpp_proxy.state.current_state() == bad_state:
            self._logger.error("%s reports state '%s'", self._xmpp_proxy, bad_state)
            system_status = False

        if not self._xmpp_dime.is_alive():
            self._logger.error("%s thread ist dead", self._xmpp_dime)
            system_status = False

        return system_status


if __name__ == "__main__":
    lib.helper.kickstart(XmppDimeRunner)