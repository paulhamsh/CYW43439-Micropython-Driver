import bluetooth
import time

from ble_advertising import advertising_payload
from micropython import const
from machine import Pin

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_INDICATE_DONE = const(20)
_IRQ_GATTS_WRITE = const(3)

_FLAG_READ = const(0x0002)
_FLAG_NOTIFY = const(0x0010)
_FLAG_INDICATE = const(0x0020)


_MIDI_IO = (
    bluetooth.UUID("7772E5DB-3868-4112-A1A9-F2669D106BF3"),
    bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY | bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE,
)

_MIDI_UUID = bluetooth.UUID("03B80E5A-EDE8-4B33-A751-6CE34EC4C700")
_MIDI_SERVICE = (
    _MIDI_UUID,
    (_MIDI_IO,),
)

class BLEMidiPeripheral:
    def __init__(self, ble, name="PicoMidi"):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._handle_io,),) = self._ble.gatts_register_services((_MIDI_SERVICE,))
        self._ble.gatts_set_buffer(self._handle_io, 32, True)
        print("Handle ", self._handle_io)
        self._connections = set()
        self._write_callback = None
        self._payload = advertising_payload(name=name, services=[_MIDI_UUID])
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_INDICATE_DONE:
            conn_handle, value_handle, status = data
        elif event == _IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)

            if self._write_callback:
                self._write_callback(value)

    def send(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_io, data)

    def is_connected(self):
        return len(self._connections) > 0

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def on_write(self, callback):
        self._write_callback = callback
        
    def set_value(self, data):
        self._ble.gatts_write(self._handle_io, data, False)

###############
        
def demo():
    midi_rx_queue = []
    
    def ble_received(bt_bytes):
        midi_rx_queue.append(bt_bytes)

    ble = bluetooth.BLE()
    peripheral= BLEMidiPeripheral(ble)
    peripheral.on_write(ble_received)
    ble_send_bytes = bytearray([0x80, 0x80, 0xB0, 0x10, 0x00])
    ble_read_bytes = bytearray([0x80, 0x80, 0xB0, 0x10, 0x7F])
    # write the local value of this handle, different value from the notify value - because we can
    peripheral.set_value(ble_read_bytes) 
    
    counter = 0
    led = Pin('LED', Pin.OUT)
    
    while True:
        if counter % 10 == 0:
            peripheral.send(ble_send_bytes)
        while midi_rx_queue:
            message = midi_rx_queue[0]
            print("MIDI bytes received: {0}".format(message.hex()))
            del midi_rx_queue[0]
        led.toggle()
        time.sleep_ms(500)
        counter += 1

if __name__ == "__main__":
    demo()
