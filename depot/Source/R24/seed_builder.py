"""Copy the two approved R23 authoring functions into an editable successor."""
from pathlib import Path
import ast
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT.parent/'KIAH_R23_Jet_Center_Refinement_R19/source/build_r23.py').read_text()
tree=ast.parse(text)
funcs='\n\n'.join(ast.get_source_segment(text,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['materials','save','model'])
funcs=funcs.replace('r23_','r24_').replace('NRT PRIVATE HANGAR','INDOOR PARKING').replace('NRT JET CENTER','NRT VIRTUAL HEADQUARTERS')
funcs=funcs.replace("'PRIVATE AVIATION','NRT']","'PRIVATE AVIATION','NRT','NRT11','HELIPAD ACCESS','HOLD / ROTORS','MAX WINGSPAN 66 FT / 20 M']")
# Atlas has 11 rows; retain 144 px per row and extend its canvas to 2048 px high.
start=funcs.index("    names=");end=funcs.index('\ndef save')
atlas=funcs[start:end].replace('(2048,1024)','(2048,2048)').replace('/1024','/2048')
funcs=funcs[:start]+atlas+funcs[end:]
for old,new in [('301.7','312.7'),('306.1','317.1'),('301.9','312.9'),('303.76','314.76'),('303.96','314.96'),('305.9','316.9'),('300.8','311.8'),('307.2','318.2'),('300.7','311.7'),('307.3','318.3'),('301.4','312.4'),('306.4','317.4')]:
    funcs=funcs.replace(old,new)
funcs=funcs.replace("2512.08,359,15.1,28,1.9","2512.08,359,17.1,28,1.9")
funcs=funcs.replace("2673.52,312,7.7","2673.52,323,7.7").replace("2673.52,298,7.7","2673.52,309,7.7").replace("2673.52,298,8.65","2673.52,309,8.65").replace("2673.52,312,8.65","2673.52,323,8.65")
funcs=funcs.replace("('NRT10',[2675,457.5],9,0)","('NRT10',[2675,457.5],9,0),('NRT11',[2671.5,431],9,90)")
funcs=funcs.replace('[(2646,303),(2650,303)]','[(2646,314),(2650,314)]').replace('[301.5,306.2]','[312.5,317.2]')
header='''"""R24 approved canopy pull-through and campus refinements. File-based only."""
from pathlib import Path
import importlib.util,json,math,re,shutil,sys,hashlib,xml.etree.ElementTree as ET,ast
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
PREV=ROOT.parent/'KIAH_R23_Jet_Center_Refinement_R19'
s=importlib.util.spec_from_file_location('r23',PREV/'source/build_r23.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.g;np=b.np;Image=b.Image;ImageDraw=b.ImageDraw;ImageFont=b.ImageFont
box=b.box;Point=b.Point;Polygon=b.Polygon;LineString=b.LineString;union=b.union
NAME='KIAH_NRT_R24_Pullthrough_Refinements_R21'
PACK=ROOT/'package'/NAME;OUT=ROOT/'output';QA=ROOT/'qa';OLD=PREV/'package/KIAH_NRT_R23_Jet_Center_Refinement_R19'
FOOT=b.FOOT;CANOPY=b.CANOPY;COLS=b.COLS;HELI=b.HELI
APPROVED=ROOT.parents[1]/'feasibility/KIAH_Canopy_Pullthrough_R24_Preview_R01/output/Measurements.json'
PROPOSAL=json.loads(APPROVED.read_text())['proposal']
NG=PROPOSAL['nosewheel'];DOOR=PROPOSAL['terminal_door'];HEAD=180
GA_NG=[2695.,431.];GA_HEAD=90.;GA_BOX=box(2674,418,2700,444)
GA_PLANNING=dict(length=22.,span=20.,nose_offset=3.,wheelbase=7.5)
# East-facing parking keeps the aircraft centered on the same GA location.
# A smooth main-gear lane change joins the shared tangent to the final east
# approach; derive nosewheel positions, including gear lead through the bend.
def ga_route():
    length=GA_PLANNING['wheelbase'];x0=g.SPINE+40.-length;x1=2667.5
    shift=GA_NG[1]-420.;points=[]
    for t in np.linspace(0,1,math.ceil((x1-x0)/.10)):
        y=420.+shift*(6*t**5-15*t**4+10*t**3)
        slope=shift*(30*t**4-60*t**3+30*t**2)/(x1-x0)
        forward=np.array([1.,slope]);forward/=np.linalg.norm(forward)
        points.append((np.array([x0+(x1-x0)*t,y])+length*forward).tolist())
    points.append(GA_NG)
    return points
GA_ROUTE=ga_route()
# Wrap the stepped building perimeter, then pass EAST of the GA stand.
# The existing west-facing pedestrian door is retained; no wall crossing.
WALK=[(2673.4,365),(2671,365),(2671,374.5),(2721,374.5),(2721,451),(2675,451),(2675,455)]
GA_WALK=[(2693,451),(2693,444)]
BLAST_PATHS=[[(3150.4,280),(2890.4,280)],[(3147.95,547),(3147.95,497),(3148.0,478),(3150.4,280)],[(2842.5,759.75),(3070,759.75)]]
REF_LEFT='nrt/kiah/r24/indoor_parking/left_open';REF_RIGHT='nrt/kiah/r24/indoor_parking/right_open'
g.PACK=PACK;g.OUT=OUT;g.QA=QA;g.placements=[];g.meshes=[];g.checks=[];g.changes=[]
BASE=json.loads((OLD/'Build_Evidence.json').read_text())
BASE_DSF=g.ag.parse_dsf(PREV/'qa/R23_Roundtrip.txt')
PLACEMENTS={q['resource']:dict(resource=q['resource'],origin=[q['geom'].x,q['geom'].y],heading=float(q['lines'][0].split()[-1])) for q in BASE_DSF['entities'] if q['kind']=='object' and q['resource'].startswith('objects/nrt_test/')}
g.B={'placements':list(PLACEMENTS.values())}
retired=[];native=[];paint_cleanup=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare():
    if (ROOT/'NRT_KIAH_R24_Test.zip').exists():raise RuntimeError('Sealed R24: create a successor')
    for p in [OUT,QA,ROOT/'reference',PACK]:p.mkdir(parents=True,exist_ok=True)
    hashes={p.relative_to(OLD).as_posix():sha(p) for p in OLD.rglob('*') if p.is_file()}
    snapshot=ROOT/'reference/R23_Hashes.json'
    if snapshot.exists():assert json.loads(snapshot.read_text())==hashes,'Baseline changed'
    else:snapshot.write_text(json.dumps(hashes,indent=2))
    shutil.copytree(OLD,PACK,dirs_exist_ok=True)
    shutil.copy2(APPROVED,ROOT/'reference/Approved_Pullthrough.json')
'''
tail="\n\n"+(ROOT/'source/refinements.py').read_text()+"\nif __name__=='__main__':main()\n"
(ROOT/'source/build_r24.py').write_text(header+'\n'+funcs+tail)
print('Seeded editable R24 builder')
