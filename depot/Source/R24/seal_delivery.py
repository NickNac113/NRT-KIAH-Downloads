from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];PACK=ROOT/'package/KIAH_NRT_R24_Pullthrough_Refinements_R21';OUT=ROOT/'output'
assert json.loads((OUT/'Installer_Validation.json').read_text())['passed']
assert all(c['passed'] for c in json.loads((OUT/'Validation.json').read_text())['checks'])
hashes=json.loads((OUT/'Package_Hashes.json').read_text());archive=ROOT/'NRT_KIAH_R24_Test.zip'
assert not archive.exists(),'Do not overwrite a sealed delivery'
for rel,h in hashes.items():assert hashlib.sha256((PACK/rel).read_bytes()).hexdigest()==h,rel
extra=['Install R24.ps1','Install R24.cmd','Check OpenSAM.ps1','Check OpenSAM.cmd','output/Package_Hashes.json','output/Install_and_Test.txt','output/Review.html','output/R24_Plan.png','output/Canopy_Pullthrough.png','output/Headquarters_Arrival.png','output/Indoor_Parking_Open.png','output/Indoor_Parking_Split.png','output/Validation.json','output/Installer_Validation.json','output/Change_List.json']
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for rel in sorted(hashes):z.write(PACK/rel,'package/'+PACK.name+'/'+rel)
    for rel in extra:z.write(ROOT/rel,rel)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for rel,h in hashes.items():assert hashlib.sha256(z.read('package/'+PACK.name+'/'+rel)).hexdigest()==h
receipt=dict(archive=str(archive),bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),package_files=len(hashes),offline_checks_passed=True,installed=False,published=False,runtime_tested=False)
(OUT/'Delivery_Receipt.json').write_text(json.dumps(receipt,indent=2));(ROOT/(archive.name+'.sha256')).write_text(receipt['sha256']+'  '+archive.name+'\n')
(ROOT/'STATUS.txt').write_text('R24 SEALED TEST DELIVERY. Exported geometry, OpenSAM bindings, unchanged airport functions, isolated installer and ZIP hashes verified. Not installed or published. R23 public feed unchanged. Simulator acceptance pending.\n')
print(json.dumps(receipt,indent=2))
