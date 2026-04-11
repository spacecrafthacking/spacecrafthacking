import struct
from cds import cds_time_now
from spp import SpacePacket

class PUSTelecommandPacket(SpacePacket):
    def __init__(self, apid, ack_flags, service_type, service_subtype,
                  source_id, sequence_count=0, source_data=b"", 
                  error_control=b""):
        
        self.ack_flags = ack_flags
        self.service_type = service_type
        self.service_subtype = service_subtype
        self.source_id = source_id
        
        secondary_header = struct.pack(
            ">BBBH",
            (2 << 4) | (ack_flags & 0xF),  # PUS version + ack flags
            service_type & 0xFF,
            service_subtype & 0xFF,
            source_id & 0xFFFF
        )
        packet_data = secondary_header + source_data + error_control

        super().__init__(
            apid=apid, sequence_flags=0b11,
            sequence_count=sequence_count,
            data_length=len(packet_data),
            packet_data_field=packet_data,)
        self.packet_type = 1
        self.secondary_header_flag = 1

if __name__ == "__main__":
    cds_time_tag = cds_time_now()
    packet = PUSTelecommandPacket(
        apid=801, ack_flags=0b1111, service_type=4, service_subtype=10,
        source_id=99, source_data="SayHello".encode("utf-8"),)
    print("PUS telecommand packet (hex):")
    print(packet.build().hex(" "))
