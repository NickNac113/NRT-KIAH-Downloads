"""Seal a review archive without installing or touching either GitHub feed."""
from common import *
import zipfile
from html.parser import HTMLParser

FILES=['Review.html','Review.txt','Terminal_B_Overview.png','Terminal_B_Gate_Detail.png',
       'Terminal_B_Passenger_Windows.png','Terminal_B_Evening.png','Terminal_B_Taxi_Plan.png']

class References(HTMLParser):
    def __init__(self):super().__init__();self.refs=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        if 'src' in a:self.refs.append(a['src'])
        if 'href' in a:self.refs.append(a['href'])

def main():
    archive=ROOT/'NRT_KIAH_R28_Review.zip'
    assert not archive.exists(),'Sealed review exists; do not overwrite.'
    validation=json.loads((ROOT/'qa/Validation.json').read_text())
    assert validation['status']=='PASS'
    assert snapshot(PREV)==json.loads((ROOT/'reference/R27_Hashes.json').read_text())
    files=[p for p in PACK.rglob('*') if p.is_file()]
    assert not any(p.name.startswith('skunkcrafts_updater') for p in files)
    forbidden=('Term_modern1_ALB_inspect.png','Term_modern1_LIT_inspect.png','Preview_Meshes.json.gz')
    parser=References();parser.feed((ROOT/'output/Review.html').read_text(encoding='utf-8'))
    for ref in parser.refs:
        if ref.startswith('https://'):continue
        if ref.startswith('#'):assert ref[1:] in parser.ids;continue
        if ref=='../NRT_KIAH_R28_Review.zip':continue
        assert (ROOT/'output'/ref).resolve().is_file(),ref
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files:z.write(p,p.relative_to(PACK.parent).as_posix())
        for name in FILES:
            p=ROOT/'output'/name
            if name=='Review.html':
                s=p.read_text(encoding='utf-8').replace('../NRT_KIAH_R28_Review.zip','../README_TEST_INSTALL.txt').replace('Download the local R28 review ZIP','Read test-install notes')
                z.writestr('Review/'+name,s)
            else:z.write(p,'Review/'+name)
        for name in ['Validation.json','Preview_Method.json']:
            z.write(ROOT/'qa'/name,'qa/'+name)
        z.write(PACK/'README_R28.txt','README_TEST_INSTALL.txt')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert not any(any(f in n for f in forbidden) for n in z.namelist())
        assert not any(n.startswith(('source/','reference/')) for n in z.namelist())
        for p in files:
            name=p.relative_to(PACK.parent).as_posix()
            assert hashlib.sha256(z.read(name)).hexdigest()==sha(p),name
        names=z.namelist()
    digest=sha(archive)
    (ROOT/'SHA256SUMS.txt').write_text(digest+'  '+archive.name+'\n')
    evidence=dict(revision='R28',status='sealed review - not installed or published',archive=archive.name,
                  archive_sha256=digest,archive_bytes=archive.stat().st_size,archive_entries=len(names),
                  package_files=len(files),package_bytes=sum(p.stat().st_size for p in files),
                  zip_crc='PASS',payload_hashes='PASS',local_review_links='PASS',raw_atlases_excluded=True,
                  source_history_excluded=True,updater_configuration_included=False,package_hashes=snapshot(PACK))
    (ROOT/'qa/Review_Package.json').write_text(json.dumps(evidence,indent=2))
    (ROOT/'STATUS.txt').write_text('R28 sealed for review.\n267/267 offline checks passed.\nArchive CRC and payload hashes passed.\nRuntime acceptance pending.\nNot installed. Not published.\nProtected baseline: R27.\n')
    print(json.dumps({k:v for k,v in evidence.items() if k!='package_hashes'},indent=2))

if __name__=='__main__':main()
