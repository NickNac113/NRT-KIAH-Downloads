import pathlib,json,hashlib,shutil,zipfile,html
ROOT=pathlib.Path(__file__).resolve().parents[1];NAME='KIAH_2026-10-24_Review_R03_HF06';STAGE=ROOT/'staged'/NAME;PRE=ROOT/'previews-final'
SOURCE=pathlib.Path(r'C:\Users\Nick\Documents\Codex\2026-10-24\cou\outputs\KIAH_2026-10-24_Review_R03_HF05')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
validation=json.loads((ROOT/'HF06_Validation.json').read_text());changes=json.loads((ROOT/'HF06_Changes.json').read_text());long=json.loads((ROOT/'HF06_Long_Aircraft_Check.json').read_text())
assert validation['passed']==validation['total'] and all(r['minimum_clearances_m'][0][1]>4.5 for r in long)
inputs=json.loads((ROOT/'work/native-review-inputs.json').read_text());assert inputs['After']==sha(STAGE/'Earth nav data/apt.dat')
margin=long[-1]['minimum_clearances_m'][0][1]
notes=f'''KIAH R03 HF06 - JETWAY JOINTS, B NORTH TAXI LANE, EA VATSIM VARIANT
24 October 2026
STAGED FOR REVIEW. NOT INSTALLED. SIMULATOR TEST PENDING.

CHANGES FROM HF05
* Add circular fixed connectors at the native moving pivots of all 32 rebuilt
  fixed jetway extensions. The original fixed bridge/sign geometry is retained.
  All 116 animated jetway records remain identical to HF05.
* Replace the angled circulation line near B15/B16/B17 with a straight lane
  between the two B piers and rounded arrival/departure connections to NB.
  Native paint and aircraft routes share the same points. NB's existing
  eastbound direction is retained. The inner endpoint moves 10 m east to
  provide clearance behind B11. Route category C remains (36 m wingspan).
* Remove the two rows of 11 red barriers from EA, and add aircraft links through
  NB, EC, ED and EE. Pavement, painted centerline and signs remain in place.
  This is the user's requested VATSIM variant despite the real-world closure.
  EA is bidirectional category E in this simulator package. That is a modeling
  choice, not a claim about current real-world or ZHOU direction restrictions.

REFERENCE AND CONFIDENCE
The United Terminal B gallery image c04-op1.jpg supports a straighter central
lane with rounded outer connections. The linked rendering was uploaded in
October 2024. It is a design reference, not a surveyed as-built paint chart.
The exact lane location and 30 m connection radius are our modeled solution.
https://www.iahbunited.com/gallery?pgid=ln2798ht2-ed8e1d6d-e544-45b0-b04e-0dcfa765ef2b

AEP: WHAT HAPPENED AND HOW FUTURE REFINEMENTS ARE PROTECTED
AEP supplies both library material replacements and separate airport overlays.
Its Houston overlay contains an older rounded asphalt footprint and snow layer.
Our earlier polygon-exclusion records used the wrong coordinate separators and
winding. The offline audit had accepted that wrong format, so its prior success
did not prove X-Plane would suppress the overlay. HF05 corrected our exclusions
to WED's exporter format and removed underlying obsolete native asphalt.
The user has now confirmed the unwanted surfaces are gone with AEP enabled.

HF06 preserves every HF05 exclusion property exactly. It does not change or
redistribute AEP assets. The included read-only compatibility check validates
exclusion syntax and reviewed coverage, AEP asset/configuration fingerprints,
and KIAH's priority above AEP. A changed AEP version triggers review rather than
being silently accepted. AEP's actively written runtime log is ignored.
Any future terminal/apron footprint change also needs a spatial overlay audit;
an unchanged compatibility baseline alone cannot approve a new work area.
See Sources/HF06_Repair/AEP_Compatibility_Workflow.txt.

VALIDATION AND LIMITS
{validation['passed']}/{validation['total']} targeted offline checks pass. Runtime edits are limited to 32 fixed
connector objects, apt.dat and two DSF tiles. All other DSF placements match the
source exactly after decoding. Runways, pavement, signs, service routes, starts,
and moving jetways remain unchanged. EA's route and B's revised lane connect.

The B lane was checked with sampled generic aircraft outlines: 36 m span and
40 m, 45 m, then 56 m length. For the longer checks, category-C parked outlines
were stretched as well. The 56 m case has {margin:.2f} m minimum sampled separation
from modeled parked aircraft. This checks the revised lane, not simultaneous
compatibility of every neighboring gate or every aircraft type. Aircraft
steering, tail swing between samples, terrain, pushback and jetway docking
still need X-Plane tests. These are custom checks, not WED validation.

PREVIEW METHOD
The before/after D5 views and B overview render actual exported custom objects
and stock animated jetway meshes in their parked state. Surface materials,
lighting and retained building massing are simplified. AEP surface effects,
terrain relief, traffic and service equipment are omitted. The route maps
come from final native airport data. No preview is an HF06 simulator screenshot.

FIRST TESTS AFTER APPROVED INSTALL
1. At D5, inspect the fixed/moving joint parked, then dock and retract. Also
   inspect a B gate and one of A20/C12/C14/C15 for the same repaired connection.
2. Taxi the B central lane in your A321 or comparable aircraft, checking the
   B15/B16/B17 side and opposite B8 side. Test the rounded connections with NB.
   Use separate clearance tests for a long 757; the static proxy is not a live
   handling test. Inspect behind B11 during pushback and taxi.
3. With AEP enabled, check that the obsolete rounded asphalt island and its
   markings/lights remain absent after a complete scenery load.
4. Inspect EA at NB and EE: both red barricade rows should be gone. Taxi via
   EC/ED as appropriate for the simulation; follow the online controller.

INSTALLATION AND PROVENANCE
This is a complete successor for the single existing R03 KIAH add-on slot.
After approval, back up HF05 and replace that slot while X-Plane is closed.
Do not enable two KIAH revisions together. No install, restart or scenery
reload was performed to prepare this revision. HF05 remains installed.
Sources contains historical notes and audit copies, not a portable rebuild.
Run revise_b_lane.py in the preserved HF06 workspace for the complete rebuild;
repair_hf06.py alone is an intermediate step and does not include the B revision.
The compatibility_guard.py utility is portable with its adjacent baseline JSON.

TECHNICAL REFERENCES
https://github.com/X-Plane/xptools/blob/master/src/WEDImportExport/WED_DSFExport.cpp#L1447-L1480
https://developer.x-plane.com/?article=customizable-jetways
https://houston.center/brief/kiah
The Houston guide does not independently establish today's EA closure status.
The user's explicit VATSIM preference is the authority for opening EA here.
'''
shutil.copy2(SOURCE/'README.txt',STAGE/'Sources/R03_HF05_historical_notes.txt')
(STAGE/'README.txt').write_text(notes,encoding='utf-8')
src=STAGE/'Sources/HF06_Repair';src.mkdir(exist_ok=True)
for p in (ROOT/'work').glob('*.py'):shutil.copy2(p,src/p.name)
for p in (ROOT/'work/AEP_Compatibility_Baseline.json',ROOT/'HF06_Changes.json',ROOT/'HF06_Validation.json',ROOT/'HF06_Long_Aircraft_Check.json'):shutil.copy2(p,src/p.name)
workflow='''AEP compatibility workflow for future KIAH refinements

1. Keep KIAH in its single top-priority add-on slot, above AEP and AEP Overlays.
2. Run the read-only compatibility guard against the staged successor package:
   python compatibility_guard.py --package "PATH TO STAGED KIAH" --xplane "X:\\X-Plane 12"
3. A red result requires investigation. The expected exclusion digest protects
   the reviewed HF05 coverage. Changed AEP files mean a new overlay/library
   audit is needed. Do not update the baseline simply to get a green result.
4. For new/rebuilt footprints, decode both airport and AEP tiles. Check overlay
   categories and the point-triggered whole-primitive exclusion behavior.
   Extend exclusions only as necessary; check effects outside the work area.
5. Validate library references and native surfaces too. DSF exclusions do not
   disable AEP's material substitutions for library assets used by KIAH itself.
6. Preserve FILTER command order, coordinate pools, and unrelated placements
   when writing DSFs. Decode the final binary and compare it with the source.
7. Produce previews and offline validation, obtain installation approval, then
   verify in X-Plane with AEP enabled. Runtime feedback remains the final test.

The baseline ignores only AEP/plugins/AEP-Live/AEP-Live Log.txt because the
running simulator writes it. No other asset, configuration or plugin file is
ignored. The guard changes no scenery or library file.
'''
(src/'AEP_Compatibility_Workflow.txt').write_text(workflow,encoding='utf-8')
method=dict(revision='HF06',game_capture=False,airport_data_inputs=inputs,scope='Actual exported custom OBJ8 and native parked moving-jetway meshes. Simplified surfaces and lighting; no AEP effects, terrain, docking or traffic simulation.',images={'01_D5_Before.png':'HF05 offline asset render','02_D5_After.png':'HF06 offline asset render','03_B_North_Route.png':'Final airport data with 56 m by 36 m generic footprint stress check','04_B_North_After.png':'HF06 offline asset render','05_EA_VATSIM.png':'Final routes and removed barrier positions'},runtime_input_hashes={p.relative_to(STAGE).as_posix():sha(p) for folder in ('objects','textures','Earth nav data') for p in (STAGE/folder).rglob('*') if p.is_file()})
(PRE/'Preview_Method.json').write_text(json.dumps(method,indent=2));shutil.copy2(PRE/'Preview_Method.json',src/'Preview_Method.json')
for p in (ROOT/'HF06_Changes.json',ROOT/'HF06_Validation.json',ROOT/'HF06_Long_Aircraft_Check.json'):shutil.copy2(p,PRE/p.name)
(PRE/'Readme.txt').write_text(notes,encoding='utf-8')
checks=''.join('<li>'+html.escape(c['check'])+'</li>' for c in validation['checks'])
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>KIAH HF06 Review</title>
<style>*{box-sizing:border-box}body{margin:0;background:#eff2f0;color:#23363b;font:17px/1.6 system-ui,sans-serif}header{background:#183c43;color:#fff;padding:48px max(5vw,24px)}header p{max-width:900px;color:#d2e2df}h1{font-size:clamp(32px,5vw,58px);line-height:1.1;margin:14px 0}h2{font-size:28px;line-height:1.25}h3{font-size:20px}main{max-width:1280px;margin:auto;padding:26px}section{margin:24px 0 36px;padding:28px;background:white;border-radius:14px;box-shadow:0 4px 18px #1c363b09}img{width:100%;height:auto;display:block;border-radius:8px}a{color:#087b80}nav a{display:inline-block;margin:0 18px 0 0;color:#cff7e8}.badge{display:inline-block;padding:5px 13px;background:#a7e2c7;color:#153a36;border-radius:24px;font-size:14px;font-weight:700}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.card{border-left:3px solid #1c9390;padding:5px 18px}.caption{font-size:14px;color:#597074;margin-top:8px}.split{display:grid;grid-template-columns:1fr 1fr;gap:18px}button{cursor:pointer;border:1px solid #287c80;background:white;color:#155256;padding:9px 18px;border-radius:8px;font:inherit}button.active{background:#155256;color:white}.tools{display:flex;gap:12px;margin:16px 0}.note{border-left:4px solid #b2933b;background:#faf6e9;padding:14px 18px}li{margin:8px 0}details{border-top:1px solid #ddd;padding:16px 0}summary{cursor:pointer;font-weight:700}@media(max-width:760px){.grid,.split{grid-template-columns:1fr}section{padding:18px}main{padding:12px}}
</style><header><span class="badge">HF06 · STAGED FOR REVIEW · NOT INSTALLED</span><h1>KIAH: connected jetways,<br>a clearer B apron, open EA.</h1><p>Three focused repairs to HF05, with the AEP protection retained. These are offline geometry previews; X-Plane testing follows an approved installation.</p><nav><a href="#joints">Jetway joints</a><a href="#taxi">B North taxi lane</a><a href="#ea">East Cargo EA</a><a href="#aep">AEP compatibility</a><a href="#tests">Checks and testing</a></nav></header><main>
<div class="grid"><div class="card"><b>32 fixed joints repaired</b><br>116 moving jetways preserved.</div><div class="card"><b>Paint and routes agree</b><br>Straight central lane with rounded NB connections.</div><div class="card"><b>22 EA barricades removed</b><br>NB–EC–ED–EE route restored for your VATSIM variant.</div></div>
<section id="joints"><h2>D5: the missing connection is filled</h2><p>The old fixed extension stopped short of the moving tunnel. A round connector now surrounds the native pivot so the tunnel can rotate while maintaining overlap. The same repair applies to the 32 rebuilt extensions.</p><div class="tools"><button class="active" id="after" onclick="swap(true)">HF06 repaired</button><button id="before" onclick="swap(false)">HF05 before</button></div><a id="jointLink" href="02_D5_After.png"><img id="joint" src="02_D5_After.png" alt="D5 with the repaired circular jetway connector"></a><p class="caption" id="jointCaption">HF06 offline asset render. Actual exported fixed object and stock moving jetway, shown parked.</p></section>
<section id="taxi"><h2>B15/B16/B17: replace the angled bend</h2><p>The straight lane between the two piers and rounded connections follow the arrangement visible in your <a href="https://www.iahbunited.com/gallery?pgid=ln2798ht2-ed8e1d6d-e544-45b0-b04e-0dcfa765ef2b">United Terminal B gallery reference</a>. NB keeps its existing eastbound direction. The line and AI route use identical points.</p><p class="note">The supplied image is an architectural rendering uploaded in 2024. It supports the arrangement; it does not establish the exact position of today's painted centerline. The location and connection radii remain modeled.</p><a href="03_B_North_Route.png"><img src="03_B_North_Route.png" alt="HF06 straight taxi lane and swept aircraft footprint compared with removed HF05 bend"></a><p>The inner end was shifted 10 metres east to clear B11 in the longer-aircraft check. With generic moving and parked aircraft expanded to 56 metres long and 36 metres span, minimum sampled clearance is <b>MARGIN metres</b>. The 45-metre case also passes. Actual turning and pushback still need a simulator test.</p><a href="04_B_North_After.png"><img src="04_B_North_After.png" alt="Offline overhead view of HF06 B North"></a><p class="caption">Final exported airport geometry. Surface appearance is simplified and AEP effects are not rendered.</p></section>
<section id="ea"><h2>East Cargo EA: open in this simulator variant</h2><p>Both rows of 11 red barricades are removed. The existing pavement, paint and signs stay in place. Added bidirectional aircraft links connect EA through NB, EC, ED and EE.</p><a href="05_EA_VATSIM.png"><img src="05_EA_VATSIM.png" alt="Map of the two EA barrier rows removed and restored taxi links"></a><p class="note">This implements your requested VATSIM preference despite the real-world closure. It is not a claim that EA has reopened in real life or that ZHOU prescribes this exact routing direction.</p></section>
<section id="aep"><h2>Why AEP's old surfaces appeared</h2><p>AEP contains a Houston overlay with the older rounded asphalt footprint and a matching snow layer. Our earlier exclusion records had incorrectly formatted coordinates and winding. The earlier offline check accepted that error, allowing us to overstate the protection. HF05 corrected our export and removed obsolete native asphalt beneath it; your latest test confirms the unwanted surfaces are gone.</p><p><b>HF06 retains all those exclusions unchanged.</b> AEP stays enabled and its files are untouched. A new read-only compatibility check flags changed AEP assets, changed exclusion coverage or incorrect scenery order before future refinements. New work areas also require an overlay coverage audit. This guards against a repeat; it is not a guarantee that an unknown future AEP update needs no review.</p></section>
<section id="tests"><h2>CHECKCOUNT targeted offline checks passed</h2><p>HF05 remains installed. HF06 has not been loaded in X-Plane. Preview lighting, pavement appearance and retained building massing are approximate; there is no docking, terrain, traffic or service simulation here.</p><h3>First tests after installation</h3><ol><li>At D5, inspect the parked joint, dock, then retract. Check a B gate too.</li><li>Taxi the B central lane and both rounded connections, inspecting clearance near B15–B17, B8 and behind B11. Test long aircraft separately.</li><li>Keep AEP enabled and confirm the obsolete island textures, lights and markings remain absent.</li><li>Inspect both ends of EA, then taxi through EC/ED as appropriate for the online session.</li></ol><details><summary>Offline validation details</summary><ul>CHECKS</ul><p><a href="HF06_Validation.json">Validation report</a> · <a href="HF06_Long_Aircraft_Check.json">Longer aircraft check</a> · <a href="Preview_Method.json">Preview inputs and limits</a> · <a href="Readme.txt">Complete revision notes</a></p></details></section>
</main><script>function swap(after){let f=after?'02_D5_After.png':'01_D5_Before.png';document.getElementById('joint').src=f;document.getElementById('jointLink').href=f;document.getElementById('after').classList.toggle('active',after);document.getElementById('before').classList.toggle('active',!after);document.getElementById('jointCaption').textContent=(after?'HF06 repaired':'HF05 before')+' — offline asset render, moving jetway shown parked.'}</script></html>'''
page=page.replace('MARGIN',f'{margin:.1f}').replace('CHECKCOUNT',str(validation['total'])).replace('CHECKS',checks)
(PRE/'Review.html').write_text(page,encoding='utf-8')
manifest=STAGE/'SHA256SUMS.txt'
manifest.write_text('\n'.join(sha(p)+'  '+p.relative_to(STAGE).as_posix() for p in sorted(STAGE.rglob('*')) if p.is_file() and p!=manifest)+'\n',encoding='utf-8')
archive=ROOT/(NAME+'.zip')
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in STAGE.rglob('*'):
        if p.is_file():z.write(p,NAME+'/'+p.relative_to(STAGE).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for p in STAGE.rglob('*'):
        if p.is_file():assert hashlib.sha256(z.read(NAME+'/'+p.relative_to(STAGE).as_posix())).hexdigest()==sha(p)
print(json.dumps(dict(package=str(archive),sha256=sha(archive),checks=validation['total'],status='READY FOR PREVIEW; NOT INSTALLED'),indent=2))
