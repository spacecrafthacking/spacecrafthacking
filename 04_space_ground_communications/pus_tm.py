import struct
from cds import cds_time_now
from spp import SpacePacket

class PUSTelemetryPacket(SpacePacket):
    def __init__(self, apid, service_type, service_subtype, destination_id,
                 time_tag, message_counter=0, pus_version=2, time_status=0,
                 sequence_count=0, source_data=b"", error_control=b""):

        self.service_type = service_type
        self.service_subtype = service_subtype
        self.destination_id = destination_id
        self.message_counter = message_counter
        self.time_status = time_status

        primary_fields = struct.pack(
            ">BBBHH",
            # PUS version + time status
            ((pus_version & 0xF) << 4) | (time_status & 0xF),
            # Masking to enforce field width
            service_type & 0xFF,
            service_subtype & 0xFF,
            message_counter & 0xFFFF,
            destination_id & 0xFFFF,
        )
        packet_data = primary_fields + bytes(time_tag) + source_data \
                        + error_control

        super().__init__(
            apid=apid, sequence_flags=0b11,
            sequence_count=sequence_count,
            data_length=len(packet_data),
        packet_data_field=packet_data,)
        self.packet_type = 0
        self.secondary_header_flag = 1

if __name__ == "__main__":
    cds_time = cds_time_now()
    packet = PUSTelemetryPacket(
        apid=801,sequence_count=17, service_type=3, service_subtype=25,
        destination_id=66, time_tag=cds_time, time_status=1,
        message_counter=5, source_data="HelloWorld".encode("utf-8"),)
    print("PUS telemetry packet (hex):")
    print(packet.build().hex(" "))
