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


logging.basicConfig(level=logging.INFO,
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

            if self._message_queue.full():
                msg.reply("can not synthetisize your message, too many messages pending").send()
                return

            if len(msg['body']) > self.MAX_MESSAGE_SIZE:
                msg.reply("received message is too long (%d chars, max: %d), "
                          "won't say anyting" % (len(msg['body']), self.MAX_MESSAGE_SIZE)).send()
                return

            # FIXME: using copy here due to reuse of msg object for response
            msg_cpy = copy.copy(msg)
            self._message_queue.put(msg_cpy)

            msg.reply("received message '%s' - enqueued to synthesize... "
                      "(queue fill level: %d / %d)" % (msg['body'].strip(),
                                                       self._message_queue.qsize(),
                                                       self._message_queue.maxsize)).send()


class Dime(lib.helper.StoppableThread):

    def __init__(self, synthesizer, xmpp_msg_filter, event_queue_size=4):
        super(Dime, self).__init__()
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self._event_queue = queue.Queue(maxsize=event_queue_size)
        self._speech_synth = lib.synth.SpeechSynth(synthesizer=synthesizer)
        self._xmpp_msg_filter = xmpp_msg_filter()

    @property
    def event_queue(self):
        return self._event_queue

    def check_system(self):
        return self._speech_synth.check_system()

    def run(self):
        self._logger.info("running, waiting on event queue...")
        while not self.stopped():
            try:
                queue_element = self._event_queue.get(timeout=1)
            except queue.Empty:
                self._logger.debug("timeout on empty queue, continue")
                continue

            text_to_say = self._xmpp_msg_filter.get_text(queue_element)
            if not self._speech_synth.say(text_to_say):
                self._logger.error("could not say '%s' using synthesizer"
                                   " '%s'!", text_to_say, self._speech_synth)

        self._logger.info("exit gracefully")


class DimeRunner(object):

    def __init__(self, cfg):
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self._dime_config = cfg
        synthesizer = eval(cfg["system"]["synthesizer"])
        msg_f = eval(cfg["system"]["msg_filter"])

        self._dime = Dime(synthesizer=synthesizer,
                          xmpp_msg_filter=msg_f)
        self._xmpp_proxy = MessageProxyXMPP(self._dime_config["xmpp"]["jid"],
                                            self._dime_config["xmpp"]["pwd"],
                                            self._dime.event_queue)

    def __del__(self):
        self._logger.debug("destructor called")
        self.stop()

    def start(self):
        if not self._dime.check_system():
            raise Exception("dime system not ready, exit immediately")
        self._dime.start()
        self._xmpp_proxy.connect()
        self._xmpp_proxy.process(block=False)

    def stop(self):
        if self._xmpp_proxy:
            self._xmpp_proxy.abort()
        if self._dime:
            self._dime.stop()
            self._dime.join()

    def is_up_and_running(self):
        system_status = True

        bad_state = "disconnected"
        if self._xmpp_proxy.state.current_state() == bad_state:
            self._logger.error("%s reports state '%s'", self._xmpp_proxy, bad_state)
            system_status = False

        if not self._dime.is_alive():
            self._logger.error("%s thread ist dead", self._dime)
            system_status = False

        return system_status


if __name__ == "__main__":
    LOGGER.info("starting application")

    PARSER = argparse.ArgumentParser(description='start dime application')
    PARSER.add_argument('--config', help='define a JSON config file')
    ARGS = PARSER.parse_args()

    if not ARGS.config:
        PARSER.print_help()
        sys.exit(1)

    CFG = None
    with open(ARGS.config, 'r') as cfg_file:
        CFG = json.load(cfg_file)

    DIME_RUNNER = DimeRunner(CFG)
    try:
        DIME_RUNNER.start()
    except Exception as exception:
        LOGGER.error(exception)
        sys.exit(1)

    while True:
        try:
            LOGGER.debug("in main idle loop")
            if not DIME_RUNNER.is_up_and_running():
                break

            time.sleep(1)

        except KeyboardInterrupt:
            LOGGER.info("KeyboardInterrupt caught, shut application down")
            break

    DIME_RUNNER.stop()
    LOGGER.info("exit gracefully")
