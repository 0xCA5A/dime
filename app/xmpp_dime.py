# pylint: disable=line-too-long

import logging
import copy
from sleekxmpp import ClientXMPP
from sleekxmpp.exceptions import IqError, IqTimeout

import lib.synth
import lib.helper
import lib.interface
import lib.msg_proc


class MessageProxyXMPP(ClientXMPP):

    MAX_MESSAGE_SIZE = 256

    def __init__(self, jid, password):
        super(MessageProxyXMPP, self).__init__(jid, password)
        self._logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self._target_event_queue_list = []

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

            for event_queue in self._target_event_queue_list:
                if self.event_queue.full():
                    msg.reply("too many messages pending, drop message").send()
                    continue

                # FIXME: using copy here due to reuse of msg object for response
                msg_cpy = copy.copy(msg)
                event_queue.put(msg_cpy)
                msg.reply("process message '%s' " % (msg['body'].strip()).send())

    def check_system(self):
        self._logger.warning("dummy implementation")
        return True

    def register_target_event_queue(self, event_queue):
        self._target_event_queue_list.append(event_queue)


class XmppDime(lib.helper.Dime):
    def __init__(self, msg_proc, event_queue_size=4):
        super(XmppDime, self).__init__(msg_proc=msg_proc, event_queue_size=event_queue_size)


class XmppDimeRunner(lib.interface.DimeRunner):
    def __init__(self, cfg):
        super(XmppDimeRunner, self).__init__()

        self._xmpp_dime_config = cfg

        self._speech = None
        self._xmpp_dime = None
        self._xmpp_proxy = None

    def start(self):
        obj_name = self._xmpp_dime_config["dime"]["synthesizer"]
        synth_type = lib.helper.get_obj_type(obj_name)
        obj_name = self._xmpp_dime_config["dime"]["msg_proc"]
        msg_proc = lib.helper.get_obj_type(obj_name)

        self._speech = lib.synth.Speech(msg_queue_size=5, synthesizer=synth_type)
        self._xmpp_dime = XmppDime(msg_proc=msg_proc, event_queue_size=2)
        self._xmpp_proxy = MessageProxyXMPP(self._xmpp_dime_config["xmpp"]["jid"],
                                            self._xmpp_dime_config["xmpp"]["pwd"])

        if not self._speech.check_system():
            raise Exception("synthesizer not ready, exit immediately")
        if not self._xmpp_dime.check_system():
            raise Exception("dime not ready, exit immediately")
        if not self._xmpp_proxy.check_system():
            raise Exception("xmpp proxy not ready, exit immediately")

        # register synth message queue at dime
        self._xmpp_dime.register_target_txt_queue(self._speech.text_queue)

        # register dime event queue at proxy
        self._xmpp_proxy.register_target_event_queue(self._xmpp_dime.event_queue)

        self._xmpp_proxy.connect()
        self._xmpp_proxy.process(block=False)

        # FIXME: xmpp state not ready
        import time
        time.sleep(1)

        self._xmpp_dime.start()
        self._speech.start()

        self._speech.text_queue.add("system successfully started - ready for take off!")

    def stop(self):
        if self._xmpp_proxy:
            self._xmpp_proxy.abort()
        if self._xmpp_dime:
            self._xmpp_dime.stop()
            self._xmpp_dime.join()
        if self._speech:
            self._speech.stop()
            self._speech.join()

    def is_up_and_running(self):
        system_status = True

        bad_state = "disconnected"
        if self._xmpp_proxy and self._xmpp_proxy.state and self._xmpp_proxy.state.current_state() == bad_state:
            self._logger.error("%s reports state '%s'", self._xmpp_proxy, bad_state)
            system_status = False

        if self._xmpp_dime and not self._xmpp_dime.is_alive():
            self._logger.error("%s thread ist dead", self._xmpp_dime)
            system_status = False

        if self._speech and not self._speech.is_alive():
            self._logger.error("%s thread ist dead", self._speech)
            system_status = False

        return system_status


if __name__ == "__main__":
    lib.helper.kickstart(XmppDimeRunner)
