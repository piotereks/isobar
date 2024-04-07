#!/usr/bin/env python3

#------------------------------------------------------------------------
# Prints all received MIDI messages to the console.
# Demonstrates the use of callbacks to generate events when MIDI
# messages are received.
#------------------------------------------------------------------------

from isobar_ext import *
import logging
import time

def main():
    def print_message(message):
        """
        The callback argument is a mido Message object:
        https://mido.readthedocs.io/en/latest/messages.html
        """
        print(" - Received MIDI: %s" % message)

    midi_in = MidiInputDevice()
    midi_in.callback = print_message
    print("Opened MIDI input: %s" % midi_in.device_name)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
    main()