"""Prepare a versioned local test installer and hash manifest; never install."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'KIAH_R22_Original_Garage_R18';PACK=ROOT/'package/KIAH_NRT_R23_Jet_Center_Refinement_R19'
v=json.loads((ROOT/'output/Validation.json').read_text());assert all(c['passed'] for c in v['checks'])
s=(OLD/'Install R22.ps1').read_text(encoding='utf-8').replace('R22','R23').replace('Original_Garage_R18','Jet_Center_Refinement_R19')
s=s.replace("$inserted = $false\n",'')
s=s.replace("        if (-not $inserted) { $newLines.Add($selectedLine); $inserted = $true }\n",'')
s=s.replace("if (-not $inserted) {\n",'{\n')
s=s.replace("'Keep your existing MisterX Library and OpenSAM installation. In-simulator tests remain pending.'", "'Keep your existing MisterX Library and OpenSAM installation. Fully exit and relaunch X-Plane, then load KIAH. Run Check OpenSAM.cmd after the session. Runtime checks remain pending.'")
# A plain script block would not execute in PowerShell; use an explicit do/while once.
s=s.replace("\n{\n    $index = 0", "\ndo {\n    $index = 0").replace("    $newLines.Insert($index,$selectedLine)\n}", "    $newLines.Insert($index,$selectedLine)\n} while ($false)")
s=s.replace("[IO.File]::WriteAllLines($iniPath,$newLines,[Text.UTF8Encoding]::new($false))", """if (@($newLines | Where-Object { $_ -eq $selectedLine }).Count -ne 1) { throw 'Expected exactly one selected R23 entry.' }
if ($newLines[$index] -ne $selectedLine -or -not $selectedLine.EndsWith('/')) { throw 'Selected scenery entry is invalid.' }
[IO.File]::WriteAllLines($iniPath,$newLines,[Text.UTF8Encoding]::new($false))""")
(ROOT/'Install R23.ps1').write_text(s,encoding='utf-8')
(ROOT/'Install R23.cmd').write_text('@echo off\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install R23.ps1"\npause\n')
test=(OLD/'qa/test_installer.ps1').read_text().replace('R22','R23').replace('Original_Garage_R18','Jet_Center_Refinement_R19')
test=test.replace("if ($first.IndexOf('Unrelated Above') -gt $first.IndexOf('KIAH_NRT_R23') -or $first.IndexOf('MisterX_Library') -lt $first.IndexOf('KIAH_NRT_R23')) { throw 'Unrelated priority changed.' }", "if ($first.IndexOf('Unrelated Above') -lt $first.IndexOf('KIAH_NRT_R23') -or $first.IndexOf('MisterX_Library') -lt $first.IndexOf('Unrelated Above')) { throw 'NRT was not placed first or unrelated relative order changed.' }")
test=test.replace('SCENERY_PACK Custom Scenery/KIAH_NRT_R20_Open_Hangars_R16/`r`n','SCENERY_PACK Custom Scenery/NRT_KIAH_Campus`r`nSCENERY_PACK Custom Scenery/KIAH_NRT_R20_Open_Hangars_R16/`r`n')
test=test.replace("'unrelated order preserved'","'NRT first, unrelated relative order preserved','missing-slash stable predecessor disabled'")
(ROOT/'qa/test_installer.ps1').write_text(test,encoding='utf-8')
src=PACK/'Source/R23';src.mkdir(parents=True,exist_ok=True)
for p in (ROOT/'source').glob('*.py'):shutil.copy2(p,src/p.name)
shutil.copy2(ROOT/'qa/R23_South.txt',src/'South.dsf.txt')
shutil.copy2(ROOT/'output/OpenSAM_Diagnosis.json',src/'OpenSAM_Diagnosis.json')
(src/'README.txt').write_text('R23 authoring source and exact native DSF input. Scripts use the private workspace R21/R17 helper modules and Laminar command-line tools. These are authoring records, not an automatic source build on a member PC. Native library assets are referenced, never redistributed. Original procedural R23 material generation is in build_r23.py.\n')
hashes={p.relative_to(PACK).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in PACK.rglob('*') if p.is_file()}
(ROOT/'output/Package_Hashes.json').write_text(json.dumps(hashes,indent=2))
print(json.dumps(dict(prepared=True,files=len(hashes),installed=False)))
