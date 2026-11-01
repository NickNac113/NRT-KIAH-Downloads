"""Seal and verify the reviewed R26 test package; does not install/publish."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];PACK=ROOT/'package/KIAH_NRT_R26_Lighting_Access_R23';OUT=ROOT/'output'
validation=json.loads((OUT/'Validation.json').read_text());installer=json.loads((OUT/'Installer_Validation.json').read_text(encoding='utf-8-sig'))
assert installer['passed'] and all(c['passed'] for c in validation['checks'])
hashes=json.loads((OUT/'Package_Hashes.json').read_text());archive=ROOT/'NRT_KIAH_R26_Test.zip'
assert not archive.exists(),'Do not overwrite a sealed delivery'
for rel,h in hashes.items():assert hashlib.sha256((PACK/rel).read_bytes()).hexdigest()==h,rel
extra=['Install R26.ps1','Install R26.cmd','Check OpenSAM.ps1','Check OpenSAM.cmd','output/Package_Hashes.json','output/Install_and_Test.txt','output/Review.txt','output/R26_Lighting_Service_Plan.png','output/R26_NRT9_Clearance.png','output/R26_Terminal_Fixtures.png','output/R26_Hangar_Fixtures.png','output/Validation.json','output/Installer_Validation.json','output/Change_List.json','output/Render_Evidence.json']
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for rel in sorted(hashes):z.write(PACK/rel,'package/'+PACK.name+'/'+rel)
    for rel in extra:z.write(ROOT/rel,rel)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for rel,h in hashes.items():assert hashlib.sha256(z.read('package/'+PACK.name+'/'+rel)).hexdigest()==h
receipt=dict(archive=str(archive),bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),package_files=len(hashes),offline_checks=validation['passed'],installer_checks=len(installer['checks']),installed=False,published=False,runtime_tested=False)
(OUT/'Delivery_Receipt.json').write_text(json.dumps(receipt,indent=2));(ROOT/(archive.name+'.sha256')).write_text(receipt['sha256']+'  '+archive.name+'\n')
(ROOT/'STATUS.txt').write_text(f'R26 SEALED LOCAL TEST. {validation["passed"]} offline checks, mock installer, complete archive and per-file hashes passed. PNG review delivered. Simulator lighting, traffic and docking tests pending. Not installed or published.\n')
print(json.dumps(receipt,indent=2))
