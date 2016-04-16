


== system configuration

{{{
root@voyage:~/share# cat ~/.asoundrc


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

}}}



== festival

https://wiki.archlinux.org/index.php/Festival

