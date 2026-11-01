from route_common import *
import shutil,hashlib,zipfile,html,csv

v=json.loads((R03/'validation.json').read_text());b=json.loads((R03/'build-report.json').read_text())
assert v['passed'],'Do not package a failed route build'
review=OUT/'KIAH_Previews_R03';sources=TARGET/'Sources';sources.mkdir(exist_ok=True)
counts=v['counts'];changes=Counter(c['type'] for c in b['changes'])
c14_distance=round(next(r['distance_m'] for r in v['manual_access_review'] if r['ramp']=='Gate C14 wide'))
shutil.copy2(BASE/'README.txt',TARGET/'R02-baseline-notes.txt')
shutil.copy2(BASE/'Sources/offline-validation.json',sources/'R02-artwork-validation.json')
for name in ['validation.json','build-report.json','Aircraft_Route_Audit.csv','Ramp_Access_Audit.csv','Service_Stand_Coverage.csv','Service_Depot_Access.csv']:
    dest='offline-validation.json' if name=='validation.json' else 'routing-build-report.json' if name=='build-report.json' else name
    shutil.copy2(R03/name,sources/dest)
    if name.endswith('.csv'):shutil.copy2(R03/name,review/name)
text=f'''KIAH — GROUND ROUTING REVIEW R03
24 October 2026
NOT INSTALLED. NOT TESTED IN X-PLANE.

RESULT
The staged full-airport scenery now contains {counts['aircraft_segments']} aircraft taxi segments and {counts['service_segments']} service-vehicle segments. All 240 aircraft starts were audited for aircraft-size-compatible directed paths to each of the five runway networks. All 226 automatically usable aircraft stands have a clear modeled connection to the adjacent network within 250 m; the longest is 228.3 m. Start locations are deliberately not joined to fixed taxi edges: X-Plane generates the final parking/pushback maneuver.

GROUND SERVICE
33 service approaches cover B North's 22 stands, D West's six primary stands, A20, C12/C14/C15 and the international processor service area. Every approach has an outbound/return path to baggage trains, baggage loaders, fuel trucks, catering, GPU and pushback vehicles. 18 new native moving-vehicle parking definitions and five circulation destinations were added. The revised terminal service network is connected; the separate GA network remains separate and does not cross runways. The total service graph has two connected components (445 and 108 nodes), down from six in R02.

AIRCRAFT NETWORK CORRECTIONS
Replaced the five R02 apron access paths using the retained aircraft envelopes as obstacles as well as new terminals. True intersections are shared nodes. Removed 11 short fixed-route spurs that entered parked-aircraft maneuvering space. Corrected {changes['direction']} inherited one-way restrictions that stranded connected routes. Applied clearance-based width restrictions and restored size-compatible links where modeled space permits; this changes routing metadata, not physical pavement width. Closed a short widebody network gap south of Terminal B. Aligned inherited runway-route nodes to their runway centerlines (largest adjustment 2.14 m). Preserved existing runway-protection and flow metadata, the reopened west taxiways and the dated EA construction closure. Painted guidance on the replaced apron paths now follows the revised routing.

CHECKS
{len(v['checks'])}/{len(v['checks'])} required offline checks pass. These cover route references, junctions, directions, all five runway networks, every aircraft start's size-compatible access, runway centerlines/protection metadata, modeled pavement and building/parked-aircraft clearance, service return paths, new vehicle parking clearance, and unchanged compiled artwork. New service-vehicle parking and destinations stay outside aircraft route wingspan clearance. Both native scenery tiles, custom models and textures are byte-identical to the validated R02 artwork; only apt.dat routing, selected apron guidance and vehicle definitions changed.

EXPLICIT SIMULATOR CHECKPOINTS
* Manual C14 wide: a class-D connection exists, but the closest connected route usable in both travel directions is {c14_distance} m away. This manual alternative's last maneuver and neighboring stand occupancy need review. No fixed route was added through occupied neighboring aircraft envelopes.
* United Maintenance 3 starts inside a hangar interior. The simplified access test excludes that interior volume; actual doorway clearance needs X-Plane testing.
* Final docking, pushback, taxi steering, vehicle avoidance, aircraft service ports, terrain fit and scenery ordering have not been tested in X-Plane.
* The obstacle test uses represented footprints and modeled aircraft envelopes, not every library object's full collision geometry. Width allowances and new service routes are modeled scenery decisions, not a surveyed airside traffic plan.
* R02's C29/E6 evidence limitations and interpreted terminal detail still apply; see R02-baseline-notes.txt.

PREVIEWS
The four new route maps are drawn from the staged native routing. The interactive review computes directed, size-aware aircraft paths and service outbound/return paths. The moving dot only illustrates a computed path; it is not X-Plane behavior. Short dashed links show final approach outside the fixed graph. R02 terminal geometry previews remain valid because those objects have not changed.

INSTALLATION HOLD
No files in X-Plane or its scenery order were changed. R01 and R02 are preserved. Installation and simulator testing remain pending the user's preview review and explicit approval.

SOURCE / REBUILD NOTES
Built on the locally preserved KIAH R02 full-airport review package and its cited Gateway/Houston Airports/FAA inputs. Native file and routing rules were checked against Laminar's documentation:
https://developer.x-plane.com/article/airport-data-apt-dat-12-00-file-format-specification/
https://developer.x-plane.com/article/atc-taxi-route-authoring/
https://developer.x-plane.com/manuals/wed/
Sources includes per-segment, per-start, service-coverage and depot-access audit tables, current validation, the R03 build report and routing scripts. Rebuilding requires the preserved R02 source inputs, their original downloads and Python geometry dependencies. Source geometry/attribution from R02 is retained. This package uses native X-Plane vehicle types and references default artwork; no third-party vehicle plugin is required by these definitions.
'''
(TARGET/'README.txt').write_text(text,encoding='utf-8');(review/'Review_Notes.txt').write_text(text,encoding='utf-8')
code=sources/'R03_Build';code.mkdir(exist_ok=True)
for name in ['route_common.py','route_build_r03.py','route_audit_r03.py','route_previews_r03.py','finish_r03.py','route_review_template.html']:
    shutil.copy2(ROOT/name,code/name)
template=(ROOT/'route_review_template.html').read_text(encoding='utf-8')
template=template.replace('27 / 27',f'{len(v["checks"])} / {len(v["checks"])}').replace('the 27 offline checks',f'the {len(v["checks"])} offline checks')
template=template.replace('321 m',f'{c14_distance} m')
template=template.replace('__CHECKS__',''.join(f'<tr><td>Pass</td><td>{html.escape(c["name"])}</td></tr>' for c in v['checks']))
template=template.replace('__DATA__',(R03/'review-data.json').read_text().replace('</',r'<\/'))
(review/'Review.html').write_text(template,encoding='utf-8')
source_text=(OUT/'KIAH_Previews_R02/Sources.html').read_text(encoding='utf-8')
extra=''.join(f'<p><a href="{u}">{t}</a></p>' for t,u in [('Laminar native airport format','https://developer.x-plane.com/article/airport-data-apt-dat-12-00-file-format-specification/'),('Laminar taxi route guidance','https://developer.x-plane.com/article/atc-taxi-route-authoring/'),('Laminar service vehicle network guidance','https://developer.x-plane.com/manuals/wed/')])
(review/'Sources.html').write_text(source_text.replace('R02','R03')+'<h2>R03 routing rules</h2>'+extra,encoding='utf-8')
# Retain the original scenery build report under an unambiguous baseline name.
shutil.copy2(BASE/'Sources/build-report.json',sources/'R02-artwork-build-report.json')
(sources/'build-report.json').write_text(json.dumps(dict(revision='R03',counts=counts,routing_report='routing-build-report.json',artwork_report='R02-artwork-build-report.json',installed=False,simulator_tested=False),indent=2))
files=[p for p in TARGET.rglob('*') if p.is_file() and p.name!='SHA256SUMS.txt']
(TARGET/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(TARGET).as_posix() for p in sorted(files))+'\n')
archive=OUT/(TARGET.name+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(TARGET.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(TARGET.parent).as_posix())
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps(dict(archive=str(archive),sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),checks=len(v['checks']),counts=counts,installed=False),indent=2))
