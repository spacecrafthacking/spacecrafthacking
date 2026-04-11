import struct
from pus_tm import PUSTelemetryPacket

class PUSTM11(PUSTelemetryPacket):
    def __init__(self, apid, destination_id, time_tag, *, message_counter=0, time_status=0,
                 sequence_count=0, tc_version_number=0, tc_secondary_header_flag=0, 
                 tc_apid=0, tc_sequence_flags=0, tc_sequence_count=0):

        self.tc_version_number = tc_version_number
        self.tc_packet_type = 1
        self.tc_secondary_header_flag = tc_secondary_header_flag
        self.tc_apid = tc_apid & 0x7FF
        self.tc_sequence_flags = tc_sequence_flags & 0x3
        self.tc_sequence_count = tc_sequence_count & 0x3FFF

        identification = (self.tc_version_number << 13) | (self.tc_packet_type << 12) | \
            (self.tc_secondary_header_flag << 11) | self.tc_apid
        sequence_control = (self.tc_sequence_flags << 14) | self.tc_sequence_count
        request_identifier = struct.pack('>HH', identification, sequence_control)

        super().__init__(apid=apid, service_type=1, service_subtype=1,
                         destination_id=destination_id, time_tag=time_tag,
                         message_counter=message_counter, time_status=time_status,
                         sequence_count=sequence_count, source_data=request_identifier,)

if __name__ == "__main__":
    from cds import cds_time_now
    cds_time_tag = cds_time_now()
    packet = PUSTM11(apid=801, destination_id=66, time_tag=cds_time_tag, time_status=1, 
                     message_counter=5, sequence_count=17, tc_version_number=0, 
                     tc_secondary_header_flag=1, tc_apid=100, tc_sequence_flags=3, 
                     tc_sequence_count=42,)
    print("PUS TM[1,1] packet (hex):")
    print(packet.build().hex(" "))
