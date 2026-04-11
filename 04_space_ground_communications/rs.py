from reedsolo import RSCodec

rsc = RSCodec(nsym=16, nsize=255)
rsc.maxerrata(verbose=True)
ORIGINAL_MESSAGE = 'Hello Satellite'

ENCODED_MESSAGE = rsc.encode(ORIGINAL_MESSAGE.encode())
print(f"Encoded Original Message: {ENCODED_MESSAGE}")
DECODED_ORIGINAL_MESSAGE = rsc.decode(ENCODED_MESSAGE)[0].decode("utf-8")
print(f"Decoded Original Message: {DECODED_ORIGINAL_MESSAGE}")
CHANGED_MESSAGE = b'Holla Satellite\xe8\x77\x8c]\xaae9z$.\xc0s\x13i$\xc4'
DECODED_CHANGED_MESSAGE = rsc.decode(CHANGED_MESSAGE)[0].decode("utf-8")
print(f"Decoded Changed Message: {DECODED_CHANGED_MESSAGE}")
