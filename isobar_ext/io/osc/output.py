from ..output import OutputDevice
from ...pattern import Pattern

try:
    from pythonosc.udp_client import SimpleUDPClient
except ModuleNotFoundError:
    pass


class OSCOutputDevice(OutputDevice):
    """
    OSCOutputDevice: Wraps MIDI messages in OSC.
    /note [ note, velocity, channel ]
    /control [ control, value, channel ]
    """

    def __init__(self, host, port):
        """
        Args:
            host: Hostname to send OSC messages to
            port: Port number to send OSC messages to
        """
        super().__init__()
        try:
            self.osc = SimpleUDPClient(host, port)

        except NameError as e:
            raise Exception("python-osc must be installed") from e

    def note_on(self, note=60, velocity=64, channel=0, **kwargs):
        # self.osc.send_message("/note", velocity, channel)
        self.osc.send_message("/note", velocity)

    def note_off(self, note=60, channel=0, **kwargs):
        # self.osc.send_message("/note", 0, channel)
        self.osc.send_message("/note", 0)

    def control(self, control, value, channel=0, **kwargs):
        # self.osc.send_message("/control", value, channel)
        self.osc.send_message("/control", value)

    def send(self, address, params=None):
        if params is not None:
            params = [Pattern.value(param) for param in params]
        self.osc.send_message(address, params)
