import queue
import time
from apscheduler.schedulers.background import BackgroundScheduler

import lib.synth
import lib.helper
import lib.interface


class ScheduleDime(lib.interface.Dime):

    SCHEDULER_SLEEP_TIME_S = 0.3

    def __init__(self, schedule_cfg, event_queue_size=4):
        super(ScheduleDime, self).__init__(event_queue_size=event_queue_size)
        self._schedule_cfg = schedule_cfg
        self._scheduler = BackgroundScheduler()

        # http://apscheduler.readthedocs.org/en/latest/modules/triggers/cron.html
        # year (int|str) – 4-digit year
        # month (int|str) – month (1-12)
        # day (int|str) – day of the (1-31)
        # week (int|str) – ISO week (1-53)
        # day_of_week (int|str) – number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)
        # hour (int|str) – hour (0-23)
        # minute (int|str) – minute (0-59)
        # second (int|str) – second (0-59)


    def _add_message_to_queue(self, text_to_say):
        for target_queue in self._target_txt_queue_list:
            try:
                target_queue.put(text_to_say)
            except queue.Full as exception:
                self._logger.error("drop message '%s': %s", text_to_say, exception)

    def job(self):
        self._logger.fatal("test")

    def run(self):
        self._logger.info("running, waiting on event queue...")

        self._scheduler.start()
        for job in self._schedule_cfg["jobs"]:
            day_of_week = job["day_of_week"]
            hour = job["hour"]
            minute = job["minute"]
            msg = job["msg"]
            self._scheduler.add_job(trigger='cron', func=self._add_message_to_queue, args=[msg],
                                    day_of_week=day_of_week,
                                    hour=hour,
                                    minute=minute)

        while not self.stopped():
            time.sleep(self.SCHEDULER_SLEEP_TIME_S)

        self._scheduler.shutdown()
        self._logger.info("exit gracefully")


class ScheduleDimeRunner(lib.interface.DimeRunner):
    def __init__(self, cfg):
        super(ScheduleDimeRunner, self).__init__()
        self._xmpp_dime_config = cfg
        self._speech = None
        self._dime = None

    def start(self):
        obj_name = self._xmpp_dime_config["dime"]["synthesizer"]
        synth_type = lib.helper.get_obj_type(obj_name)

        schedule_cfg = self._xmpp_dime_config["dime"]["schedule"]
        if not len(schedule_cfg):
            self._logger.error("no event scheduled, return")
            return

        self._speech = lib.synth.Speech(msg_queue_size=5, synthesizer=synth_type)
        self._dime = ScheduleDime(schedule_cfg=schedule_cfg,
                                  event_queue_size=2)

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
        self._speech.text_queue.put("system shutdown triggered - have a nice day!")

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
    lib.helper.kickstart(ScheduleDimeRunner)