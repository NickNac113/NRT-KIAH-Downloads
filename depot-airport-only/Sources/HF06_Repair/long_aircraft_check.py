import sys,pathlib,math,pickle,json
sys.path.insert(0,r'X:\X-Plane 12\Output\KIAH_R03_HF05_Repair\work')
from hf05_common import *
from route_common import aircraft_outline
from shapely import affinity
ROOT=pathlib.Path(__file__).resolve().parents[1];STAGE=ROOT/'staged/KIAH_2026-10-24_Review_R03_HF06'
apt=parse_apt(STAGE/'Earth nav data/apt.dat');_,lines,_,_=pickle.loads((ROOT/'work/b-lane.pkl').read_bytes())
def longplane(pos,h,length):
    g=aircraft_outline((0,0),0,'C');g=affinity.scale(g,xfact=1,yfact=length/40,origin=(0,0))
    return affinity.translate(affinity.rotate(g,-h,origin=(0,0)),*pos)
report=[]
for length,shift in [(45,0),(56,0)]:
    planes=[(a['name'],longplane(a['geom'].coords[0],a['heading'],length) if a.get('rampmeta',['1301','C'])[1]=='C' else aircraft_outline(a['geom'].coords[0],a['heading'],a.get('rampmeta',['1301','C'])[1])) for a in apt if a['code']==1300 and a['kind']!='misc']
    swept=[]
    for idx,line in enumerate(lines):
        line=affinity.translate(line,xoff=shift)
        for rev in ([False,True] if idx==0 else [False]):
            l=LineString(list(line.coords)[::-1]) if rev else line
            for d in np.linspace(0,l.length,max(2,int(l.length/1.5)+1)):
                p=l.interpolate(d);a=l.interpolate(max(0,d-.5));b=l.interpolate(min(l.length,d+.5));h=math.degrees(math.atan2(b.x-a.x,b.y-a.y));swept.append(longplane(p.coords[0],h,length))
    sweep=unary_union(swept);nearest=sorted([(n,sweep.distance(p)) for n,p in planes],key=lambda v:v[1])[:3]
    if length==56:(ROOT/'work/swept-long.pkl').write_bytes(pickle.dumps(sweep))
    report.append(dict(length_m=length,span_m=36,trial_shift_east_m=shift,minimum_clearances_m=nearest))
(ROOT/'HF06_Long_Aircraft_Check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
