"""Conservative stand and taxi-envelope study; no scenery writes."""
from pathlib import Path
import sys, importlib.util, json, math
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
PREV=ROOT.parent/'KIAH_R24_Pullthrough_Refinements_R21'
s=importlib.util.spec_from_file_location('r24',PREV/'source/build_r24.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
sys.path.insert(0,str(b.APPROVED.parents[1]/'source'));import analyze as a
np=b.np;box=b.box;Line=b.LineString;Point=b.Point;union=b.union
walk=Line(b.WALK).buffer(.8,cap_style=2,join_style=2)
heli=box(2652,457,2698,503)
path=b.PROPOSAL['arrival']+b.PROPOSAL['departure'][1:]
canopy=[]
for name in ['G650','Lineage 1000E']:
    poses,_=a.follow_path(name,path)
    canopy.append(union([a.footprint(name,p['ng'],p['heading']) for p in poses]).buffer(.1))
canopy=union(canopy)
obstacles={'HQ':b.FOOT,'Helipad':heli,'Walk':walk,'Canopy traffic':canopy,
           'NRT9 A380 envelope':box(2722.2,435,2802.1,508)}
def branch(ng,wheelbase):
    x0=b.g.SPINE+40.-wheelbase;x1=ng[0]-wheelbase-8
    out=[];shift=ng[1]-420
    for t in np.linspace(0,1,math.ceil((x1-x0)/.15)):
        y=420+shift*(6*t**5-15*t**4+10*t**3)
        slope=shift*(30*t**4-60*t**3+30*t**2)/(x1-x0)
        f=np.array([1.,slope]);f/=np.linalg.norm(f)
        out.append((np.array([x0+(x1-x0)*t,y])+wheelbase*f).tolist())
    out.append(list(ng));return out
def assess(length,span,ng,wb=18):
    a.AIRCRAFT['candidate']=dict(length=length,span=span,nose_offset=4,wheelbase=wb)
    parked=a.footprint('candidate',ng,90)
    gaps={k:parked.distance(v) for k,v in obstacles.items()}
    return gaps,parked
if __name__=='__main__':
    (ROOT/'output').mkdir(parents=True,exist_ok=True)
    rows=[]
    for length,span in [(22,20),(40,36),(50,48),(50,52),(50,60),(50,64),(50,65),(50,66),(51,65),(52,65),(54.47,41.1),(54.94,50.9)]:
        best=None
        for y in np.arange(407,421,.25):
            gaps,p=assess(length,span,[2713,y])
            d=dict(length=length,span=span,nosewheel=[2713,float(y)],gaps=gaps,min_gap=min(gaps.values()),bounds=list(p.bounds))
            if best is None or d['min_gap']>best['min_gap']:best=d
        rows.append(best)
    (ROOT/'output/Stand_Options.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps(rows,indent=2))
