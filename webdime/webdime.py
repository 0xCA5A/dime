import pycurl
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash


# create our little application :)
APP = Flask(__name__)
APP.config.update(dict(
    DEBUG=True,
))
JOBS = []
ADD_JOB_FUNCTIONS = []


def get_jobs_from_queue():
    """Replace this function to get from scheduler"""
    return JOBS

def register_add_job_function(add_job_function):
    ADD_JOB_FUNCTIONS.append(add_job_function)


def add_job_to_queue(day_of_week, hour, minute, msg):
    """Replace this function to add to scheduler"""

    element = {
        "day_of_week" : day_of_week,
        "hour" : hour,
        "minute" : minute,
        "msg" : msg
    }

    JOBS.append(element)

    for func in ADD_JOB_FUNCTIONS:
        func(element)


@APP.route('/')
def show_jobs():
    jobs = get_jobs_from_queue()
    return render_template('show_jobs.html', jobs=jobs)


@APP.route('/add', methods=['POST'])
def add_job():
    day_of_week = request.form['day_of_week']
    hour = int(request.form['hour'])
    minute = int(request.form['minute'])
    msg = request.form['msg']

    add_job_to_queue(day_of_week, hour, minute, msg)

    return redirect(url_for('show_jobs'))


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@APP.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'


def stop():

    print("called")

    c = pycurl.Curl()
    c.setopt(pycurl.URL, "127.0.0.1/shutdown")
    c.setopt(pycurl.PORT, 5000)
    c.setopt(pycurl.POST, 1)
    c.perform()


if __name__ == "__main__":
    APP.run()
