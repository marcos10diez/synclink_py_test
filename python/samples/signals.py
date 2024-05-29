# signal control and monitoring sample
#
# The RTS output should be connected to the CTS input.

import sys
import time
import threading

# mgapi module is available to import if:
# 1. mgapi package installed using pip command.
# 2. mgapi.py is in current directory or python sys path.
sys.path.append('..')  # not needed if mgapi package installed using pip
from mgapi import Port

run = True

def wait_thread_func():
    # display current CTS
    if port.cts:
        print('CTS is on')
    else:
        print('CTS is off')
    # wait for CTS changes
    while run:
        print('wait for CTS off')
        events = port.wait(Port.CTS_OFF)
        if events & Port.CTS_OFF:
            print('CTS is off')
        if not run:
            break
        print('wait for CTS on')
        events = port.wait(Port.CTS_ON)
        if events & Port.CTS_ON:
            print('CTS is on')

# port name format
# PCI: /dev/ttySLGx, x=adapter number
# USB: /dev/ttyUSBx, x=adapter number
if len(sys.argv) < 2:
    # no port name on command line, use first enumerated port
    names = Port.enumerate()
    if not names:
        print('no ports available')
        exit()
    port = Port(names[0])
else:
    port = Port(sys.argv[1])
print('signals sample running on', port.name)

try:
    port.open()
except FileNotFoundError:
    print('port not found')
    exit()
except PermissionError:
    print('access denied or port in use')
    exit()
except:
    print('open error')
    exit()

print('press Ctrl-C to stop program')
wait_thread = threading.Thread(target=wait_thread_func)
wait_thread.start()
time.sleep(1)

# RTS is on by default after open

try:
    while run:
        print('turn off RTS')
        port.rts = False
        time.sleep(1)
        print('turn on RTS')
        port.rts = True
        time.sleep(1)
except KeyboardInterrupt:
    run = False

port.close()