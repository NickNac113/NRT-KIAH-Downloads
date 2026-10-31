"""Independent export checks; does not run X-Plane or claim live acceptance."""
import ast,json,math,sys,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];CAMPUS=ROOT.parents[1]
sys.dont_write_bytecode=True
sys.path.insert(0,str(CAMPUS/'tools/python_geometry'))
sys.path.insert(0,str(ROOT.parent/'KIAH_R17_Native_Surface_R13/source'))
import airport_geometry as ag
from shapely.geometry import Polygon,Point,LineString,box
PACK=ROOT/'package/KIAH_NRT_R21_Jet_Center_R17'
OLD=ROOT.parent/'KIAH_R20_Open_Hangars_R16/package/KIAH_NRT_R20_Open_Hangars_R16'
B=json.loads((PACK/'Build_Evidence.json').read_text());D=B['jet_center'];checks=[]
def check(n,v):
 checks.append(dict(name=n,passed=bool(v)))
 if not v:raise AssertionError(n)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
src=ROOT.parent/'KIAH_R17_Native_Surface_R13/source/obj_reader.py'
tree=ast.parse(src.read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'independent_OBJ_reader','exec'))
native={}
for lib in Path('X:/X-Plane 12/Resources/default scenery').glob('*/library.txt'):
 for row in lib.read_text(errors='replace').splitlines():
  p=row.split()
  if len(p)>=3 and p[0] in ['EXPORT','EXPORT_BACKUP','EXPORT_EXTEND']:native.setdefault(p[1],lib.parent/' '.join(p[2:]))
  elif len(p)>=4 and p[0] in ['EXPORT_SEASON','EXPORT_RATIO']:native.setdefault(p[2],lib.parent/' '.join(p[3:]))
dsf=ag.parse_dsf(ROOT/'qa/R21_Roundtrip.txt')
for resource in dsf['objects']+dsf['polygons']:
 if resource.startswith('lib/'):
  check('Native resource resolves: '+resource,resource in native and native[resource].is_file())
 elif not resource.startswith('MisterX_Library/'):
  check('Local resource resolves: '+resource,(PACK/resource).is_file())
for p in (PACK/'objects').rglob('*.obj'):
 rows=[s.split() for s in p.read_text(errors='strict').splitlines()];counts=next(s for s in rows if s and s[0]=='POINT_COUNTS')
 verts=[s for s in rows if s and s[0]=='VT'];ids=[int(x) for s in rows if s and s[0] in ['IDX','IDX10'] for x in s[1:]]
 check('OBJ indices: '+p.name,len(verts)==int(counts[1]) and len(ids)==int(counts[4]) and all(0<=x<len(verts) for x in ids))
 for s in rows:
  if s and s[0] in ['TEXTURE','TEXTURE_LIT','TEXTURE_NORMAL','TEXTURE_DRAPED','TEXTURE_DRAPED_NORMAL']:
   rel=' '.join(s[2:] if s[0]=='TEXTURE_DRAPED_NORMAL' else s[1:]);check('Texture '+p.name+' '+rel,(p.parent/rel).is_file())
 check('Balanced animation: '+p.name,sum(s==['ANIM_begin'] for s in rows)==sum(s==['ANIM_end'] for s in rows))

apt=ag.parse_apt(PACK/'Earth nav data/apt.dat');oldapt=ag.parse_apt(OLD/'Earth nav data/apt.dat')
starts={s['name']:s for s in apt if s['code']==1300 and s['name'].startswith('NRT')}
check('15 main NRT starts only',len(starts)==15)
check('Retired four starts absent',not set(B['retired_starts'])&starts.keys())
for n,s in [('NRT PRIVATE HANGAR',D['hangar']['start']),('NRT CANOPY',D['canopy']['start'])]:
 q=starts[n];check(n+' heading/position',abs(q['heading']-s['heading'])<.001 and q['geom'].distance(Point(s['ng']))<.01)
for old in oldapt:
 if old['code']==1300 and old['name'] not in B['retired_starts']:
  new=next(q for q in apt if q['code']==1300 and q['name']==old['name']);check('Retained start '+old['name'],new['lines']==old['lines'])
check('Both helipads unchanged',[s['lines'] for s in apt if s['code']==102]==[s['lines'] for s in oldapt if s['code']==102])
active={q['resource'] for q in dsf['entities'] if q['kind']=='object'}
for n in ['mh3_accordion_hangar','floor_wear_mh3','signs_mh3_accordion_hangar']:check('Old MH3 not placed '+n,'objects/nrt_test/'+n+'.obj' not in active)
for item in B['new_placements']:
 matches=[q for q in dsf['entities'] if q['kind']=='object' and q['resource']==item['resource']]
 check('One compiled placement '+item['resource'],len(matches)==1 and matches[0]['geom'].distance(Point(item['origin']))<.10)
dr='nrt/kiah/r21/private_hangar/doors_open';obj=PACK/'objects/nrt_test/r21_private_hangar.obj'
open_tri,_=readobj(obj,[2473,359],vals={dr:1});closed_tri,_=readobj(obj,[2473,359],vals={dr:0})
opening=box(2510.6,290.0,2511.2,428.0)
def obstruction_count(tris):
 count=0
 for t in tris:
  if t[:,2].min()<13.9 and t[:,2].max()>.1 and 2510.6<t[:,0].mean()<2511.2 and 290.0<t[:,1].mean()<428.0:count+=1
 return count
check('Open doors leave 138 m entry clear',obstruction_count(open_tri)==0)
check('Closed doors cover the opening',obstruction_count(closed_tri)>40)
for xml in ['sam.xml','opensam.xml']:
 root=ET.parse(PACK/xml).getroot();refs=root.findall('datarefs/dataref')
 check(xml+' manual open-on-load',len(refs)==5 and all(r.get('autoplay')=='false' and [a.get('v') for a in r.findall('animation')]==['1','0'] for r in refs))
 check(xml+' new private hangar control',len([c for c in root.findall('gui/checkbox') if c.get('dataref')==dr])==1)
canopy,_=readobj(PACK/'objects/nrt_test/r21_terminal_canopy.obj',[2674,330]);clear=box(*D['canopy']['clear_box'])
low=[]
for t in canopy:
 if t[:,2].min()<14-1e-4 and clear.buffer(-.02).contains(Point(t[:,:2].mean(axis=0))):low.append(t)
check('Canopy clear volume has no structure below 14 m',not low)
for name,q in D['aircraft'].items():check(name+' exterior envelope fits canopy',q['fits_clear_box'])
for name,q in D['geometry_checks'].items():check(name+' planned aircraft tow sweep',not q['overlapping_obstacles'])

# Car path is an actual rounded loop, not a square drawing. 5.4 x 2.0 m envelope.
poses=[]
def straight(a,b):
 a=np.array(a);b=np.array(b);f=(b-a)/np.linalg.norm(b-a)
 for p in np.linspace(a,b,max(2,int(np.linalg.norm(b-a)*3))):poses.append((p,f))
straight([2737,300],[2704,300])
for angle in np.linspace(-math.pi/2,-math.pi,40):poses.append((np.array([2704,305])+5*np.array([math.cos(angle),math.sin(angle)]),np.array([math.sin(angle),-math.cos(angle)])))
straight([2699,305],[2699,319])
for angle in np.linspace(math.pi,math.pi/2,40):poses.append((np.array([2704,319])+5*np.array([math.cos(angle),math.sin(angle)]),np.array([math.sin(angle),-math.cos(angle)])))
straight([2704,324],[2737,324])
obstacles={'terminal':box(*D['terminal']['main']),'wing':box(*D['terminal']['side_wing']),'median':box(*D['landside']['median']),
 'west entrance post':box(2696.88,327.8,2697.12,328.05),'east entrance post':box(2722.88,327.8,2723.12,328.05)}
minimum=1e9;hits=[]
for p,f in poses:
 r=np.array([f[1],-f[0]]);poly=Polygon([p+f*a+r*b for a,b in [(-2.7,-1),(-2.7,1),(2.7,1),(2.7,-1)]])
 for name,b in obstacles.items():
  minimum=min(minimum,poly.distance(b))
  if poly.intersects(b):hits.append(name)
check('Passenger car rounded route avoids fixed obstacles',not hits)
check('Flag pole is inside protected median',box(*D['landside']['median']).buffer(-.3).contains(Point(D['landside']['flagpole'])))
check('Tree is inside protected median',box(*D['landside']['median']).buffer(-.3).contains(Point(D['landside']['feature_tree'])))
# Confirm fence triangles no longer bridge the opening.
fence,_=readobj(PACK/'objects/nrt_test/landside_fence.obj',[2900,500]);bad=[]
for t in fence:
 if 2719<t[:,0].mean()<2721 and 292.1<t[:,1].mean()<333.5:bad.append(t)
check('Former car park west fence opened at arrival court',not bad)
check('R20 hashes unchanged',all(sha(OLD/k)==v for k,v in json.loads((ROOT/'reference/R20_Hashes.json').read_text()).items()))
report=dict(passed=len(checks),checks=checks,passenger_car_route=dict(length_m=5.4,width_m=2.0,minimum_fixed_obstacle_gap_m=round(minimum,2),center_turn_radius_m=5,limits='Static body envelope; not vehicle steering physics'),runtime_tested=False)
(ROOT/'output/Validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(passed=len(checks),passenger_car=report['passenger_car_route'],runtime_tested=False),indent=2))
