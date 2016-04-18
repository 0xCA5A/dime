# dime - say it to me!
simple xmpp client - tts aplication. write something by jabber and he will say it!
could be used as extreme feedback device for your build environment.

features:
 * multiple instances possible (alsa mixing)
 * different synthesizer wrapper
 * different text filter to filter out bad words

## how to run
```
root@voyage:~/dime# ./runner.sh --config sally.cfg
```

simple JSON config added to select synthesizer and message filter.
```
{
    "xmpp": {
        "jid": "harry@10.0.30.10",
        "pwd": "beer"
    },
    "system": {
        "synthesizer": "synth.Espeak",
        "msg_filter": "msg_filter.XmppMsgPassthrough"
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
