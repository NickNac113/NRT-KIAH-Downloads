from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];PACK=ROOT/'package/KIAH_NRT_R23_Jet_Center_Refinement_R19';OUT=ROOT/'output'
assert json.loads((OUT/'Installer_Validation.json').read_text())['passed']
assert json.loads((OUT/'Diagnostic_Validation.json').read_text())['passed']
assert all(c['passed'] for c in json.loads((OUT/'Validation.json').read_text())['checks'])
hashes=json.loads((OUT/'Package_Hashes.json').read_text());archive=ROOT/'NRT_KIAH_R23_Test.zip'
assert not archive.exists(),'Do not overwrite a sealed delivery'
for rel,h in hashes.items():assert hashlib.sha256((PACK/rel).read_bytes()).hexdigest()==h,rel
extra=['Install R23.ps1','Install R23.cmd','Check OpenSAM.ps1','Check OpenSAM.cmd','output/Package_Hashes.json','output/Install_and_Test.txt','output/Review.html','output/Canopy_Export.png','output/Arrival_Export.png','output/Canopy_Plan.png','output/Campus_Plan.png','output/Validation.json','output/OpenSAM_Diagnosis.json','output/Installer_Validation.json','output/Diagnostic_Validation.json']
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for rel in sorted(hashes):z.write(PACK/rel,'package/'+PACK.name+'/'+rel)
    for rel in extra:z.write(ROOT/rel,rel)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for rel,h in hashes.items():assert hashlib.sha256(z.read('package/'+PACK.name+'/'+rel)).hexdigest()==h
receipt=dict(archive=str(archive),bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),files=len(hashes),offline_checks_passed=True,installed=False,runtime_tested=False,published=False,openSAM_restart_test='Deferred by user; pending')
(OUT/'Delivery_Receipt.json').write_text(json.dumps(receipt,indent=2));(ROOT/'NRT_KIAH_R23_Test.zip.sha256').write_text(receipt['sha256']+'  '+archive.name+'\n')
print(json.dumps(receipt,indent=2))
