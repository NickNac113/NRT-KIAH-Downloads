from hf05_common import *
import struct
# Polygon exclusion changes have identical string lengths. Replace only the
# PROP atom payload and recompute DSF's MD5; keep all packed placement and
# command bytes intact. This avoids DSFTool's re-quantization of headings.
for src in (SOURCE/'Earth nav data').rglob('*.dsf'):
    source=src.read_bytes();assert source[:8]==b'XPLNEDSF'
    body=source[:-16];assert hashlib.md5(body).digest()==source[-16:]
    converted=(ROOT/'work'/f'{src.stem}-hf05.txt').read_text().splitlines()
    original=(ROOT/'work'/f'{src.stem}-before.txt').read_text().splitlines()
    replacements={}
    for a,b in zip(original,converted):
        if a==b:continue
        assert a.startswith('PROPERTY sim/exclude_') and b.startswith('PROPERTY sim/exclude_')
        x=a.split(' ',2)[2].encode()+b'\0';y=b.split(' ',2)[2].encode()+b'\0'
        assert len(x)==len(y);replacements[x]=y
    if not replacements:continue
    result=bytearray(body);prop_range=None
    at=12
    while at<len(body):
        key=body[at:at+4];size=struct.unpack_from('<I',body,at+4)[0]
        assert size>=8
        if key==b'DAEH':
            p=at+8
            while p<at+size:
                sub=body[p:p+4];ss=struct.unpack_from('<I',body,p+4)[0]
                if sub==b'PORP':prop_range=(p+8,p+ss)
                p+=ss
            assert p==at+size
        at+=size
    assert at==len(body) and prop_range
    start,end=prop_range;payload=body[start:end]
    for x,y in replacements.items():
        assert payload.count(x)>0
        payload=payload.replace(x,y)
    assert len(payload)==end-start
    result[start:end]=payload
    assert result[:start]==body[:start] and result[end:]==body[end:]
    out=bytes(result)+hashlib.md5(result).digest()
    dest=STAGE/src.relative_to(SOURCE);dest.write_bytes(out)
    dsf_decode(dest,ROOT/'work'/f'{src.stem}-roundtrip.txt')
    print(src.stem,'exact geometry/commands preserved; exclusion payload bytes',len(payload),'unique corrected values',len(replacements))
