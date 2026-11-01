from sign_groups import *
from prepare_hf02 import audit,read_obj,sha
from route_common import smooth_pavement
from layout_plan import heading_vec,aircraft_outline
STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF02'
LIVE=pathlib.Path(r'X:\X-Plane 12\Custom Scenery\KIAH_2026-10-24_Review_R03')
plan,before,oldapt=pickle.loads((ROOT/'work/context.pkl').read_bytes())
apt=parse_apt(STAGE/'Earth nav data/apt.dat');dsf=parse_dsf(ROOT/'work/roundtrip-south.txt')
scene=json.loads((ROOT/'work/scene-hf02.json').read_text());details=json.loads((ROOT/'HF02_Detail_Validation.json').read_text())
checks=[]
def test(name,value,info=None):checks.append(dict(check=name,passed=bool(value),detail=info));print(('PASS ' if value else 'FAIL ')+name,info if info is not None else '')
models=[audit(p) for p in (STAGE/'objects').glob('*.obj')]
test('All custom model front faces use OBJ8 clockwise winding',all(m['clockwise_outward']==m['triangles'] and not m['degenerate'] for m in models),dict(models=len(models),triangles=sum(m['triangles'] for m in models)))
test('Airport declaration remains KIAH',len([a for a in apt if a['code']==1 and a['parts'][4]=='KIAH'])==1)
test('32 new plus 84 retained animated jetways',sum(a['code']==1500 for a in apt)==116)
bad=[]
for a in [a for a in apt if a['code']==1500][:32]:
    s=a['parts'];lo,hi=[(11,23),(14,29),(17,38),(20,47)][int(s[5])];angle=(float(s[8])-float(s[6])+180)%360-180
    if not(lo<=float(s[7])<=hi and -90.01<=angle<=.01 and 0<=int(s[4])<=3 and abs(float(s[6])-float(s[3]))<.01):bad.append(a['lines'][0])
test('All 32 newly authored jetways have valid extension and cabin rotation',not bad,bad)
global_jets={a['lines'][0] for a in parse_apt(ROOT/'work/current-global-KIAH-apt.dat') if a['code']==1500}
matched=sum(r in global_jets for r in details['restored_records'])
test('Restored jetways use current 0-based size codes',all(0<=int(x['current'])<=3 and (x['matched_current_global'] or int(x['current'])==int(x['old'])-1) for x in details['current_size_code_updates']) and set(details['restored_records'])<={a['lines'][0] for a in apt if a['code']==1500},dict(exact_current_global_records=matched,additional_source_arms=84-matched))
basefac=[e for e in dsf['entities'] if 'Jetways/' in e['resource']]
test('Restored jetways meet a surviving fixed base',all(min(e['geom'].distance(Point(xy(float(l.split()[2]),float(l.split()[1])))) for e in basefac)<1 for l in details['restored_records']))
newj=[a for a in apt if a['code']==1500][:32]
test('All new jetways meet the authored fixed tunnel bases',all(Point(xy(float(a['parts'][2]),float(a['parts'][1]))).distance(Point(j['base']))<.002 for a,j in zip(newj,scene['jetways'])))
test('Native parked headings and lengths match the designed jetway endpoints',all(Point(np.array(xy(float(a['parts'][2]),float(a['parts'][1])))+heading_vec(float(a['parts'][6]))*float(a['parts'][7])).distance(Point(j['end']))<.01 for a,j in zip(newj,scene['jetways'])))
solids=unary_union([shape(g) for g in scene['model_outlines'].values()])
pavement=unary_union([smooth_pavement(a) for a in apt if a['code']==110 and int(a['parts'][1]) not in (3,4,5,13)])
test('Custom terminal footprints have continuous hard surface underneath',solids.difference(pavement.buffer(.01)).area<.1,round(solids.difference(pavement).area,3))
label_bad=[];polys=[]
for l in details['ground_labels']:
    p=np.array(l['pos']);f=heading_vec(l['heading']);right=np.array([f[1],-f[0]])
    poly=Polygon([p+right*x+f*y for x,y in [(-l['width']/2,-l['height']/2),(l['width']/2,-l['height']/2),(l['width']/2,l['height']/2),(-l['width']/2,l['height']/2)]])
    polys.append((l['name'],poly))
    if poly.intersects(solids) or not pavement.buffer(.02).covers(poly):label_bad.append(l['name'])
test('All new ground labels lie on pavement clear of terminal buildings',not label_bad,label_bad)
overlaps=[(a,b) for i,(a,p) in enumerate(polys) for b,q in polys[i+1:] if p.intersection(q).area>.01]
test('Ground labels do not overlap each other',not overlaps,overlaps)
reversed_new=[];original={tuple(e['lines']) for e in before['entities']}
for e in dsf['entities']:
    if e['kind']!='polygon' or not any(t in e['resource'] for t in ('term_building','term_bridge','Garage')):continue
    if e['geom'].is_empty or len(e['loops'][0])<3:continue
    pts=e['loops'][0];signed=sum(x*v-u*y for (x,y),(u,v) in zip(pts,pts[1:]+pts[:1]))/2
    if signed<-.01:reversed_new.append(e['resource'])
test('All terminal and garage facade outlines face outward',not reversed_new,reversed_new)
codes={100,1000,1001,1002,1003,1004,1100,1110,1101,1201,1202,1204,1205,1206,1300,1400,1401}
test('Aircraft routes, service routes, stands, runways and flow rules unchanged',[a['lines'] for a in oldapt if a['code'] in codes]==[a['lines'] for a in apt if a['code'] in codes])
test('Installed scenery still unchanged',all(sha(LIVE/p)==h for p,h in json.loads((ROOT/'live_before.json').read_text()).items()))
test('Compiled southern DSF round-trip succeeds',bool(dsf['entities']))
test('Northern scenery tile unchanged',sha(STAGE/'Earth nav data/+30-100/+30-096.dsf')==sha(LIVE/'Earth nav data/+30-100/+30-096.dsf'))
native_new={j['name']:j for j in scene['jetways']}
stand={r['name']:r for r in scene['new_stands'] if not r.get('alternative')}
bridge_conflicts=[];parked_conflicts=[]
for name,j in native_new.items():
    fixed=LineString([j['door'],j['base']]).buffer(1.5,cap_style=2);moving=LineString([j['base'],j['end']]).buffer(1.35,cap_style=2)
    for other,r in stand.items():
        if other==name:continue
        plane=aircraft_outline(r['pos'],r['heading'],r['size'])
        if fixed.intersection(plane).area>.05:bridge_conflicts.append([name,other])
        if moving.intersection(plane).area>.05:parked_conflicts.append([name,other])
test('Fixed bridges clear neighboring modeled aircraft envelopes',not bridge_conflicts,bridge_conflicts)
test('Parked moving tunnels clear neighboring modeled aircraft envelopes',not parked_conflicts,parked_conflicts)
report=dict(revision='R03 HF02',status='STAGED - NOT INSTALLED',checks=checks,passed=sum(x['passed'] for x in checks),total=len(checks),models=models,
runtime_pending=['X-Plane roof/wall rendering including retained facades','Native jetway extension and docking at retained and rebuilt gates','Vehicle traffic, pushback and aircraft taxi maneuvers','Apron layering and terrain fit in the simulator'],
sources=['https://developer.x-plane.com/article/obj8-file-format-specification/','https://developer.x-plane.com/article/dsf-usage-in-x-plane/','https://developer.x-plane.com/article/airport-data-apt-dat-12-00-file-format-specification/'])
(ROOT/'HF02_Final_Validation.json').write_text(json.dumps(report,indent=2))
if report['passed']!=report['total']:raise SystemExit(1)
