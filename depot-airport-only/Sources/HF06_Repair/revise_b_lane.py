from repair_hf06 import ROOT,STAGE,SOURCE,plan,scene,changes
from hf05_common import *
from route_common import network,aircraft_outline
# Importing the base repair is intentional: rebuild HF06 from HF05 each run.
ROOT=pathlib.Path(__file__).resolve().parents[1];STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF06'
apt=parse_apt(STAGE/'Earth nav data/apt.dat');nodes,edges=network(apt)
oldline=next(a for a in apt if a['lines'][0]=='120 R03 aircraft circulation 106')['geom']
left=np.array(nodes[328]);right=np.array(nodes[324]);slope=(right[1]-left[1])/(right[0]-left[0])
def nby(x):return float(left[1]+(x-left[0])*slope)
cx=-375.;r=30.;middle=np.array([cx,nby(cx)-r]);arrstart=np.array([cx-r,nby(cx-r)]);depend=np.array([cx+r,nby(cx+r)])
# Move the dead-end approach point 10 m east with the straight lane. The
# former endpoint aligns behind B11 and fails the 56 m long-aircraft check.
assert sum(e['a']==856 or e['b']==856 for e in edges)==1
nodes[856]=(cx,nodes[856][1])
lon,lat=ll(*nodes[856]);moved856=f'1201 {lat:.9f} {lon:.9f} both 856 HF06 B apron inner end'
# Cubic quarter-turn transitions. Endpoints meet the NB centerline exactly;
# tangent directions follow its gentle eastward slope.
k=.5522847498307936
def cubic(p,c,d,q):return [(1-t)**3*p+3*(1-t)**2*t*c+3*(1-t)*t*t*d+t**3*q for t in np.linspace(0,1,13)]
arr=cubic(arrstart,arrstart+np.array([r*k,r*k*slope]),middle+np.array([0,r*k]),middle)
dep=cubic(middle,middle+np.array([0,r*k]),depend-np.array([r*k,r*k*slope]),depend)
branches=[arr,dep];newnodes=[];newedges=[];idmap={};nextid=max(nodes)+1
def node(p):
 global nextid
 key=tuple(round(float(v),5) for v in p)
 if key not in idmap:
  idmap[key]=nextid;lon,lat=ll(*p);newnodes.append(f'1201 {lat:.9f} {lon:.9f} both {nextid} HF06 B apron');nodes[nextid]=tuple(p);nextid+=1
 return idmap[key]
midid=node(middle);arrid=node(arrstart);depid=node(depend)
newedges.append(f'1202 856 {midid} twoway taxiway_C B North apron')
for branch in branches:
 ids=[node(p) for p in branch]
 newedges.extend(f'1202 {a} {b} oneway taxiway_C B North apron' for a,b in zip(ids,ids[1:]))
nbedges=[f'1202 328 {arrid} oneway taxiway_F NB',f'1202 {arrid} {depid} oneway taxiway_F NB',f'1202 {depid} 324 oneway taxiway_F NB']
newpaint=[]
for title,pts in [('HF06 B North straight apron lane',[nodes[856],middle]),('HF06 B North arrival curve',arr),('HF06 B North departure curve',dep)]:
 newpaint.append('120 '+title)
 for i,p in enumerate(pts):
  lon,lat=ll(*p);newpaint.append(f'{115 if i==len(pts)-1 else 111} {lat:.9f} {lon:.9f}'+(' 51' if i<len(pts)-1 else ''))
remove_edges={(856,857),(857,858),(858,328)}
rows=[]
for a in apt:
 if a['code']==120 and a['lines'][0]=='120 R03 aircraft circulation 106':rows+=newpaint
 elif a['code']==1202 and (a['start'],a['end']) in remove_edges:pass
 elif a['code']==1201 and a['id'] in (857,858):pass
 elif a['code']==1201 and a['id']==856:rows.append(moved856)
 elif a['code']==1202 and (a['start'],a['end'])==(328,324):rows+=nbedges
 else:rows+=a['lines']
at=next(i for i,l in enumerate(rows) if l.startswith('1202 '));rows[at:at]=newnodes
at=next(i for i,l in enumerate(rows) if l.startswith('1206 '));rows[at:at]=newedges
(STAGE/'Earth nav data/apt.dat').write_text('\n'.join(rows)+'\n',encoding='utf-8')
newlines=[LineString([nodes[856],middle]),LineString(arr),LineString(dep)];new=unary_union(newlines)
planes=[(a['name'],aircraft_outline(a['geom'].coords[0],a['heading'],a.get('rampmeta',['1301','C'])[1])) for a in apt if a['code']==1300 and a['kind']!='misc']
nearest=sorted([(n,g.distance(new)) for n,g in planes],key=lambda v:v[1])[:8]
changes['B15_B17_audit']['previous_alignment_action']='Replaced in HF06'
changes['B15_B17_audit']['action']='Superseded by HF06 straight lane and rounded connections.'
changes['B15_B17_revision']=dict(reference='https://www.iahbunited.com/gallery?pgid=ln2798ht2-ed8e1d6d-e544-45b0-b04e-0dcfa765ef2b',reference_file='c04-op1.jpg',reference_uploaded='2024-10-23',reference_type='architectural rendering, not an as-built survey',model='Straight central category-C apron lane with two 30m rounded NB connections; NB one-way direction retained',new_node_ids=list(idmap.values()),new_route_records=newedges+nbedges,nearest_parked_aircraft_to_centerline_m=nearest,remaining_wingtip_margin_for_36m_span_m=min(v[1] for v in nearest)-18,exact_as_built_verified=False)
(ROOT/'HF06_Changes.json').write_text(json.dumps(changes,indent=2))
(ROOT/'work/b-lane.pkl').write_bytes(pickle.dumps((oldline,newlines,arr,dep)))
print(json.dumps(changes['B15_B17_revision'],indent=2))
