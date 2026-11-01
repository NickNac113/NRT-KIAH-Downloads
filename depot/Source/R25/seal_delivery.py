"""Seal and verify the reviewed local package without installing or publishing."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1];PACK=ROOT/'package/KIAH_NRT_R25_Realism_R22';OUT=ROOT/'output'
assert json.loads((OUT/'Installer_Validation.json').read_text())['passed']
assert all(c['passed'] for c in json.loads((OUT/'Validation.json').read_text())['checks'])
hashes=json.loads((OUT/'Package_Hashes.json').read_text());archive=ROOT/'NRT_KIAH_R25_Test.zip'
assert not archive.exists(),'Do not overwrite a sealed delivery'
for rel,h in hashes.items():assert hashlib.sha256((PACK/rel).read_bytes()).hexdigest()==h,rel
extra=['Install R25.ps1','Install R25.cmd','Check OpenSAM.ps1','Check OpenSAM.cmd','output/Package_Hashes.json','output/Install_and_Test.txt','output/Review.txt','output/pdf/NRT_R25_Realism_Review.pdf','output/R25_Plan.png','output/Headquarters_Arrival.png','output/Canopy_Finish.png','output/Jetway_Connections.png','output/NRT11_Export.png','output/Validation.json','output/Installer_Validation.json','output/Change_List.json','output/Render_Evidence.json']
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for rel in sorted(hashes):z.write(PACK/rel,'package/'+PACK.name+'/'+rel)
    for rel in extra:z.write(ROOT/rel,rel)
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for rel,h in hashes.items():assert hashlib.sha256(z.read('package/'+PACK.name+'/'+rel)).hexdigest()==h
receipt=dict(archive=str(archive),bytes=archive.stat().st_size,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),package_files=len(hashes),offline_checks=235,installer_checks=8,installed=False,published=False,runtime_tested=False)
(OUT/'Delivery_Receipt.json').write_text(json.dumps(receipt,indent=2));(ROOT/(archive.name+'.sha256')).write_text(receipt['sha256']+'  '+archive.name+'\n')
(ROOT/'STATUS.txt').write_text('R25 SEALED LOCAL TEST. 235 offline checks, mock installer, complete archive and per-file hashes passed. PDF/PNG review delivered. No live appearance, weather, movement or FPS acceptance. Not installed or published; public release 0.24.0 / R24 unchanged.\n')
print(json.dumps(receipt,indent=2))
