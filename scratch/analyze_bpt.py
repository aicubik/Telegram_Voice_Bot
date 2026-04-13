import sys

with open('bp-204.bpt', 'rb') as f:
    data = f.read()

print("Length:", len(data))
print("First 100 bytes:", data[:100])

import zlib
try:
    decompressed = zlib.decompress(data)
    print("Zlib decompressed length:", len(decompressed))
    print("First 100 bytes of decompressed:", decompressed[:100])
except Exception as e:
    print("Not zlib:", e)

try:
    import gzip
    decompressed2 = gzip.decompress(data)
    print("Gzip decompressed length:", len(decompressed2))
except Exception as e:
    print("Not gzip:", e)
