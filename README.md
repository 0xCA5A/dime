# dime - say it to me!
simple application to say something triggered by an event.

 * xmpp client - tts aplication. write something by jabber and he will say it!
 * camera event - tts application. say something if a movement is detected.
 * timed event - tts application. read chuck norris facts randomly.

could be used as extreme feedback device for your build environment.

features:
 * multiple tts synthesizer instances possible (alsa mixing)
 * different synthesizer wrappers
 * different text processors to process the text before synthesis

## how to run
```
root@voyage:~/dime# ./xmpp_runner.sh --config cfg/xmpp_sally.cfg
root@voyage:~/dime# ./timed_runner.sh --config cfg/event_timed.cfg
root@voyage:~/dime# ./camera_runner.sh --config cfg/event_camera.cfg
```

a simple JSON config could look like this:
```
{
    "xmpp": {
        "jid": "sally@10.0.30.10",
        "pwd": "beer"
    },
    "dime": {
        "synthesizer": "lib.synth.Dummy",
        "msg_proc": "lib.msg_proc.XmppMsgBadWordBlaming"
    }
}
```

## demo system

### hardware
pc engines alix3d3
 * http://www.pcengines.ch/alix3d3.htm

## os
voyage linux

additional packages (and dependencies):
 * python3
 * python-pip3
 * alsa-utils


 * festival
 * festival-czech
 * festlex-cmu
 * festlex-oald
 * festlex-poslex
 * festvox-czech-ph
 * festvox-don
 * festvox-kallpc16k
 * festvox-kdlpc16k
 * festvox-rablpc16k


 * espeak


 * pico2wave


python packages from pip:
 * SleekXMPP
 * schedule

### alsa mixer configuration
to support multiple audio sources, enable the alse mixer plugin.
```
root@voyage:~/dime# cat ~/.asoundrc

pcm.!default {
    type plug
    slave.pcm "dmixer"
}
pcm.dsp0 {
    type plug
    slave.pcm "dmixer"
}
pcm.dmixer {
    type dmix
    ipc_key 1024
    slave {
        pcm "hw:0,0"
        period_time 0
        period_size 1024
        buffer_size 8192
        #periods 128
        rate 44100
     }
     bindings {
        0 0
        1 1
     }
}
ctl.mixer0 {
    type hw
    card 0
}

```

## synthesizer tested

### festival
 * https://wiki.archlinux.org/index.php/Festival

### espeak
 * http://espeak.sourceforge.net/docindex.html

### pico2wave
 * http://manpages.ubuntu.com/manpages/xenial/en/man1/pico2wave.1.html

## links
 * http://stackoverflow.com/questions/1614059/how-to-make-python-speak
 * http://askubuntu.com/questions/21811/how-can-i-install-and-use-text-to-speech-software
 * http://askubuntu.com/questions/53896/natural-sounding-text-to-speech


 * https://www.youtube.com/watch?v=cziGpZTKZko
 * https://www.youtube.com/watch?v=h2VbcoCw_oM
