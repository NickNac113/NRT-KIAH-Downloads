"""Reopen the exported DSF/OBJ/XML and check the isolated garage replacement."""
from pathlib import Path
import ast, collections, hashlib, json, math, sys
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];CAMPUS=ROOT.parents[1]
PACK=ROOT/'package/KIAH_NRT_R22_Original_Garage_R18'
OLD=ROOT.parent/'KIAH_R21_Jet_Center_R17/package/KIAH_NRT_R21_Jet_Center_R17'
sys.path.insert(0,str(CAMPUS/'tools/python_geometry'))
sys.path.insert(0,str(ROOT.parent/'KIAH_R17_Native_Surface_R13/source'))
import airport_geometry as ag
from shapely.geometry import box,Point,LineString
from shapely import wkt
src=ROOT.parent/'KIAH_R17_Native_Surface_R13/source/obj_reader.py'
tree=ast.parse(src.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'exported_OBJ_reader','exec'))
checks=[]
def check(n,ok):
    checks.append(dict(name=n,passed=bool(ok)))
    if not ok:raise AssertionError(n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
S=json.loads((PACK/'Garage_Provenance.json').read_text());B=json.loads((PACK/'Build_Evidence.json').read_text())
removed=json.loads((ROOT/'output/Removed_Donor_Assets.json').read_text());omitted={r['path'] for r in removed}
check('No garage_t02 files remain',not any(p.name.startswith('garage_t02_') for p in PACK.rglob('*')))
check('Personal-only donor marker removed',not (PACK/'PERSONAL_TEST_ONLY.txt').exists())
check('All 27 donor mesh placements removed',S['legacy_donor_instances_removed']==27)
check('Original authoring uses no donor geometry/texture input',S['input_geometry_or_texture_files']==[])
check('Original garage fits the existing cargo recess',box(3065,693,3095.18,761).covers(box(*S['bounds_en'])))
known_changed={'Earth nav data/+20-100/+29-096.dsf','Build_Evidence.json','opensam.xml','sam.xml','Source/README.txt'}
for rel,h in json.loads((ROOT/'reference/R21_Hashes.json').read_text()).items():
    check('R21 preserved '+rel,sha(OLD/rel)==h)
    if rel not in known_changed|omitted:check('Unrelated runtime/source retained '+rel,sha(PACK/rel)==h)
old=ag.parse_dsf(ROOT/'reference/R21_South.txt');new=ag.parse_dsf(ROOT/'qa/R22_Roundtrip.txt')
def signature(q):
    if q['kind']=='object':return ('object',q['resource'],*(round(v,6) for v in q['coords']))
    # Quantization can move DSF coordinates slightly. Compare named resources,
    # all polygon attributes and geographically rounded point sequences.
    rows=[]
    for line in q['lines'][1:]:
        t=line.split()
        rows.append(tuple([t[0],*(round(float(x),6) for x in t[1:])]) if t and t[0]=='POLYGON_POINT' else tuple(t))
    return ('polygon',q['resource'],q['param'],tuple(rows))
before=[q for q in old['entities'] if not Path(q['resource']).name.startswith('garage_t02_')]
after=[q for q in new['entities'] if not Path(q['resource']).name.startswith('r22_')]
check('All unrelated DSF entity identities/counts retained',len(before)==len(after) and all((a['kind'],a['resource'])==(b['kind'],b['resource']) for a,b in zip(before,after)))
# DSFTool re-quantizes the encoded coordinate pools on export. Verify the
# semantic input is unaltered and separately bound the measured roundtrip drift.
gaps=[a['geom'].hausdorff_distance(b['geom']) for a,b in zip(before,after) if not a['geom'].is_empty and not b['geom'].is_empty]
max_quantization_m=max(gaps)
check('DSF coordinate roundtrip stays below 25 cm',max_quantization_m<.25)
check('Unrelated DSF headings and polygon attributes retained',all(a['coords'][2:]==b['coords'][2:] if a['kind']=='object' else (a['param']==b['param'] and a['lines'][0].split()[2:]==b['lines'][0].split()[2:]) for a,b in zip(before,after)))
input_dsf=ag.parse_dsf(ROOT/'qa/R22_South.txt')
unchanged_input=[q for q in input_dsf['entities'] if not Path(q['resource']).name.startswith('r22_')]
check('Unrelated DSF source coordinates exactly retained',collections.Counter(signature(q) for q in before)==collections.Counter(signature(q) for q in unchanged_input))
check('Donor object definitions removed, not just hidden',not any('garage_t02_' in r for r in new['objects']))
for p in S['new_placements']:
    placed=[q for q in new['entities'] if q['resource']==p['resource']]
    check('One new placement '+p['resource'],len(placed)==1 and placed[0]['geom'].distance(Point(p['origin']))<.05)
for r in new['objects']+new['polygons']:
    if not r.startswith(('lib/','MisterX_Library/')):check('DSF file reference '+r,(PACK/r).is_file())
for path in (PACK/'objects').rglob('*.obj'):
    rows=[s.split() for s in path.read_text().splitlines()];verts=[q for q in rows if q and q[0]=='VT'];indices=[int(x) for q in rows if q and q[0] in ('IDX','IDX10') for x in q[1:]]
    counts=next(q for q in rows if q and q[0]=='POINT_COUNTS')
    check('OBJ indices '+path.name,len(verts)==int(counts[1]) and len(indices)==int(counts[4]) and all(0<=i<len(verts) for i in indices))
    for q in rows:
        if q and q[0] in ('TEXTURE','TEXTURE_LIT','TEXTURE_NORMAL','TEXTURE_DRAPED','TEXTURE_DRAPED_NORMAL'):
            ref=' '.join(q[2:] if q[0]=='TEXTURE_DRAPED_NORMAL' else q[1:]);check('Texture reference '+path.name+' '+ref,(path.parent/ref).is_file())
    check('OBJ animation stack '+path.name,sum(q==['ANIM_begin'] for q in rows)==sum(q==['ANIM_end'] for q in rows))

base=[3080,727];doors=PACK/'objects/nrt_test/r22_nrt_truck_doors.obj';shell=PACK/'objects/nrt_test/r22_nrt_truck_garage.obj'
refs=[p['dataref'] for p in S['service_bays']]
door_states={}
for value in [0,.25,.5,.75,1]:
    tris,_=readobj(doors,base,vals={r:value for r in refs});door_states[value]=tris
    check(f'All moving door sections stay inside the workshop at {value}',tris[:,:,0].min()>3087 and tris[:,:,0].max()<3095.15 and tris[:,:,2].min()>-.01 and tris[:,:,2].max()<6.5)
opened=door_states[1];closed=door_states[0]
check('Open panels are above 5.8 m clear openings',opened[:,:,2].min()>5.8)
for b in S['service_bays']:
    cy=b['center_y'];t=closed[(closed[:,:,1].mean(axis=1)>cy-4.01)&(closed[:,:,1].mean(axis=1)<cy+4.01)]
    check(b['id']+' closed panel coverage',t[:,:,1].max()-t[:,:,1].min()>=7.99 and t[:,:,2].max()-t[:,:,2].min()>5.75)
    clear=box(*b['clear_box']);obstruct=[];tri,_=readobj(shell,base)
    # Remove floor/ceiling and retain only actual below-clearance structural
    # triangles. Flat vertical faces are tested by their projected edges too.
    for t in tri:
        if t[:,2].max()<.15 or t[:,2].min()>5.8:continue
        if clear.buffer(-.02).contains(Point(t[:,:2].mean(axis=0))):obstruct.append(t)
    check(b['id']+' floor-to-door-height clear work volume',not obstruct)
    # A straight, aligned 24.5 x 2.6 m tractor/trailer proxy fits the bay.
    vehicle=box(3068,cy-1.3,3092.5,cy+1.3)
    check(b['id']+' 24.5 m aligned truck envelope fits',clear.covers(vehicle))
for filename in ['sam.xml','opensam.xml']:
    r=ET.parse(PACK/filename).getroot();prev=ET.parse(OLD/filename).getroot()
    for oldref in prev.findall('datarefs/dataref'):
        nr=next(q for q in r.findall('datarefs/dataref') if q.get('name')==oldref.get('name'))
        check('Existing aircraft hangar control retained '+oldref.get('name')+' '+filename,ET.tostring(nr).strip()==ET.tostring(oldref).strip())
    for ref in refs:
        item=next(q for q in r.findall('datarefs/dataref') if q.get('name')==ref)
        check('Manual open default '+ref+' '+filename,item.get('autoplay')=='false' and [q.get('v') for q in item.findall('animation')]==['1','0'])
        check('Independent Close control '+ref+' '+filename,len([q for q in r.findall('gui/checkbox') if q.get('dataref')==ref])==1)
# Previously measured parking reverse sweeps stay clear of the replacement.
previous=ROOT.parent/'KIAH_R17_Native_Surface_R13/output/Truck_Clearance.json'
report=json.loads(previous.read_text());gaps={}
for b in report['bays']:
    g=wkt.loads(b['sweep_wkt']);gap=g.distance(box(*S['bounds_en']));gaps[b['id']]=round(gap,2)
    check('Existing occupied-yard reverse sweep clears garage '+b['id'],gap>0)
check('Marked garage forecourt and through lane remain clear',box(*S['bounds_en']).disjoint(box(*B['landside']['garage_forecourt'])) and box(*S['bounds_en']).disjoint(box(*B['landside']['truck_central_aisle'])))
donor_hashes={r['sha256'] for r in removed if Path(r['path']).name.startswith('garage_t02_')}
check('No donor binary hashes survive under renamed files',not any(sha(p) in donor_hashes for p in PACK.rglob('*') if p.is_file()))
result=dict(passed=len(checks),checks=checks,parking_sweep_gap_to_replacement_m=gaps,maximum_dsf_roundtrip_quantization_m=max_quantization_m,truck_bay_envelope='24.5 x 2.6 m, straight aligned only. A turn into the workshop is not a truck-physics validation.',runtime_tested=False)
(ROOT/'output/Validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='checks'},indent=2))
