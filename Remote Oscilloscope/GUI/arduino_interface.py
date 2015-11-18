import serial
import serial.tools.list_ports
import time
import struct

def find_arduino_ports():
    serial_ports = []
    for (port, port_name, port_desc) in serial.tools.list_ports.comports():
        if ("VID:PID=2341:0043" in port_desc):
            serial_ports += [port]
    return serial_ports

#################################################################################
class TwoChannelADC:
    def __init__(self, serial_port):
        self.serial = serial.Serial(serial_port, 115200, timeout=None)
        self.buffer = b''
        
    def close(self):
        self.serial.close()

    def reset_command(self):
        for i in range(10):
            self.serial.write(b'r')
            time.sleep(0.01)

    def start_command(self):
        # wait for Arduino serial to start and then empty buffer
        self.reset_command()      # send reset command
        self.serial.write(b's')   # send "s" to Arduino
        self.serial.flushInput()  # flush the input buffer for a clean start

    def clear_buffer(self):
        self.buffer = b''

    def read_adc(self, is_8bit = True):
        self.buffer += self.serial.read(3) # read 3 bytes

        if (len(self.buffer) > 3): # if we have enough in the buffer
            #byte1 = ord(self.buffer[0]) # 2k
            #byte2 = ord(self.buffer[1]) # 2k
            #byte3 = ord(self.buffer[2]) # 2k
            byte1 = self.buffer[0] # 3k
            byte2 = self.buffer[1] # 3k
            byte3 = self.buffer[2] # 3k

            # the start byte should have its MSB == 0, rest should MSB = 1
            if (((byte1 & 0x80) != 0x00) or
                ((byte2 & 0x80) != 0x80) or
                ((byte3 & 0x80) != 0x80)):
                self.buffer = self.buffer[1:]
                return None # return None, if received bad things

            # get the bytes from raw value
            val1 = (byte3 & 0x7f) + ((byte2 & 0x07) << 7)
            val2 = ((byte2 & 0x78) >> 3) + ((byte1 & 0x3f) << 4)

            # 10 bit to 8 bit
            if is_8bit:
                val1 = int(val1 / 4)
                val2 = int(val2 / 4)
            else:
                val1 = int(val1)
                val2 = int(val2)

            # discard the used parts of buffer
            self.buffer = self.buffer[3:]
            
            # return the good values
            return (val1, val2)
        else:
            # not enough in buffer, send empty
            return None

    def int_to_bytestring(self, val):
        #s1 = chr(val >> 8) + chr(val & 0xff) # 2k
        s1 = bytes([val >> 8, val & 0xff]) # 3k
        return s1

    def double_to_bytestring(self, val):
        return struct.pack('d', val)
