# pylint: disable=line-too-long

import queue
import time
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

import lib.synth
import lib.helper
import lib.interface


APP = Flask(__name__)
APP.config.update(dict(
    DEBUG=True,
))

JOBS = [
                    {
                        "day_of_week" : "mon-fri",
                        "hour" : 9,
                        "minute" : 40,
                        "msg" : "daily scrum starts in 5 minutes - get ready guys!"
                    },
                    {
                        "day_of_week" : "mon-fri",
                        "hour" : 9,
                        "minute" : 45,
                        "msg" : "daily scrum starts now!"
                    },
                    {
                        "day_of_week" : "mon-fri",
                        "hour" : 9,
                        "minute" : 59,
                        "msg" : "one minute left!"
                    },
                    {
                        "day_of_week" : "mon-fri",
                        "hour" : 10,
                        "minute" : 0,
                        "msg" : "daily scrum time is over - go and get a coffee!"
                    }
                ]


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



    @staticmethod
    def get_jobs_from_queue():
        """Replace this function to get from scheduler"""
        return JOBS

    def add_job_to_queue(self, day_of_week, hour, minute, msg):
        """Replace this function to add to scheduler"""
        JOBS.append({
            "day_of_week" : day_of_week,
            "hour" : hour,
            "minute" : minute,
            "msg" : msg
        })

    @staticmethod
    @APP.route('/')
    def show_jobs():
        jobs = ScheduleDime.get_jobs_from_queue()
        return render_template('show_jobs.html', jobs=jobs)


    @staticmethod
    @APP.route('/add', methods=['POST'])
    def add_job():
        day_of_week = request.form['day_of_week']
        hour = int(request.form['hour'])
        minute = int(request.form['minute'])
        msg = request.form['msg']

        ScheduleDime.add_job_to_queue(day_of_week, hour, minute, msg)

        return redirect(url_for('show_jobs'))

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

        if not APP:
            self._logger.error("something went wrong with flask")
            return


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

        # while not self.stopped():
        #     time.sleep(self.SCHEDULER_SLEEP_TIME_S)



        APP.run(debug=True, use_reloader=False)
        # this code here will never be reached...

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