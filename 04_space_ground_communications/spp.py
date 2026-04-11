import struct

class SpacePacket:
    def __init__(self, version_number=0, packet_type=0, secondary_header_flag=0,
                 apid=0, sequence_flags=3, sequence_count=0, data_length=0,
                 packet_data_field=b''):
        self.version_number = version_number
        self.packet_type = packet_type
        self.secondary_header_flag = secondary_header_flag
        self.apid = apid & 0x7FF
        self.sequence_flags = sequence_flags & 0x3
        self.sequence_count = sequence_count & 0x3FFF
        self.data_length = data_length
        self.packet_data_field = packet_data_field

    def build(self):
        # Primary Header (6 bytes)
        identification = (self.version_number << 13) | (self.packet_type << 12) | \
                           (self.secondary_header_flag << 11) | self.apid
        sequence_control = (self.sequence_flags << 14) | self.sequence_count
        packet_length = (self.data_length - 1) & 0xFFFF
        header = struct.pack('>HHH', identification, sequence_control, packet_length)
        return header + self.packet_data_field

if __name__ == "__main__":
    data = b'HelloWorld'
    pkt = SpacePacket(apid=42, data_length=12, packet_data_field=data)
    packet_bytes = pkt.build()
    print("Built CCSDS Space Packet (hex):", packet_bytes.hex(' '))
