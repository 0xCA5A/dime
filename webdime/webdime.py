"""
webdime
"""

import os
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash


# create our little application :)
app = Flask(__name__)
app.config.update(dict(
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



def get_jobs_from_queue():
    """Replace this function to get from scheduler"""
    return JOBS


def add_job_to_queue(day_of_week, hour, minute, msg):
    """Replace this function to add to scheduler"""
    JOBS.append({
        "day_of_week" : day_of_week,
        "hour" : hour,
        "minute" : minute,
        "msg" : msg
    })


@app.route('/')
def show_jobs():
    jobs = get_jobs_from_queue()
    return render_template('show_jobs.html', jobs=jobs)


@app.route('/add', methods=['POST'])
def add_job():
    day_of_week = request.form['day_of_week']
    hour = int(request.form['hour'])
    minute = int(request.form['minute'])
    msg = request.form['msg']

    add_job_to_queue(day_of_week, hour, minute, msg)

    return redirect(url_for('show_jobs'))


if __name__ == "__main__":
    app.run()
