import datetime as dt
import struct

# Define the start of the epoch.
CCSDS_EPOCH = dt.datetime(1958, 1, 1, tzinfo=dt.UTC)

def cds_time_now():
    # Calculate the three different time deltas.
    now = dt.datetime.now(dt.UTC)
    delta_days = (now - CCSDS_EPOCH).days
    delta_time = now.time()
    delta_ms = (
        (delta_time.hour * 3600 + delta_time.minute * 60 + delta_time.second)
        * 1000 + delta_time.microsecond // 1000
    )
    delta_micro = delta_time.microsecond % 1000
    
    # Pack the data into a [16 bit | 32 bit | 16 bit] structure.
    return struct.pack("!HIH", delta_days, delta_ms, delta_micro)

if __name__ == "__main__":
    # Print the resulting packed time in hexadecimal numbers.
    print(cds_time_now().hex())
