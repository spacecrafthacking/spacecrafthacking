import struct
from pus_tc import PUSTelecommandPacket

class PUSTC21(PUSTelecommandPacket):
    def __init__(self, apid, source_id, device_addresses, ack_flags=b'1111',
                 sequence_count=0, command_count=1):

        if isinstance(device_addresses, int):
            self.device_addresses = [device_addresses]
        elif isinstance(device_addresses, (list, tuple)):
            if not all(isinstance(addr, int) for addr in device_addresses):
                raise TypeError("All device addresses must be integers.")
            self.device_addresses = list(device_addresses)
        else:
            raise TypeError(
                "device_addresses must be an integer or a list of integers."
            )

        self.command_count = command_count
        command = struct.pack(">B", command_count) 
        for addr in self.device_addresses:
            command += struct.pack(">H", addr)

        super().__init__(
            apid=apid,
            ack_flags=ack_flags,
            service_type=2,
            service_subtype=1,
            source_id=source_id,
            sequence_count=sequence_count,
            source_data=command,
        )

if __name__ == "__main__":
    from cds import cds_time_now

    cds_time_tag = cds_time_now()
    packet = PUSTC21(apid=200, source_id=5, device_addresses=[101, 102],
                     ack_flags=0b1111, sequence_count=10, command_count=2)

    print("PUS TC[2,1] packet (hex):")
    print(packet.build().hex(" "))
