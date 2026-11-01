"""Read-only baseline access and geometry utilities for isolated R28."""
import os,sys,json,math,hashlib,ast
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
OLD=Path('C:/Users/Nick/Documents/Codex/2026-10-24/cou/work')
sys.path.insert(0,str(OLD))
import airport_geometry as ag
os.environ['MPLCONFIGDIR']=str(ROOT/'qa/mpl-cache')
import numpy as np
from shapely.geometry import Polygon,Point,LineString,MultiPoint,box,shape
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
BASE=ROOT.parent/'KIAH_R27_Shelter_Service_R24'
PREV=BASE/'package/KIAH_NRT_R27_Shelter_Service_R24'
NAME='KIAH_NRT_R28_Terminal_B_R25'
PACK=ROOT/'package'/NAME
LIB=Path('X:/X-Plane 12/Resources/default scenery/airport scenery')
DSF_SOURCE=BASE/'qa/R27_Roundtrip.txt'
DSF=ag.parse_dsf(DSF_SOURCE)
APT=ag.parse_apt(PREV/'Earth nav data/apt.dat')
REGION=box(-730,300,45,745)
KIT='lib/airport/Modern_Airports/Terminal_kit/'
GJ=json.loads(Path('X:/X-Plane 12/Custom Scenery/KIAH_2026-10-24_Review_R03/Sources/current-terminal-footprints.geojson').read_text())
B=next(ag.project(shape(f['geometry'])) for f in GJ['features'] if 'B_North' in str(f['properties']))
STARTS=[a for a in APT if a['code']==1300 and a['name'].startswith('Gate B') and a['geom'].y>320]
NODES={a['id']:ag.xy(a['lon'],a['lat']) for a in APT if a['code']==1201}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def snapshot(folder):return {p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file()}
def native_exports():
    out={}
    # Stock airport scenery only: deliberately excludes AEP overrides.
    for row in (LIB/'library.txt').read_text().splitlines():
        s=row.split(maxsplit=2)
        if len(s)==3 and s[0] in ('EXPORT','EXPORT_BACKUP','EXPORT_EXTEND'):
            out.setdefault(s[1],LIB/s[2].replace('\\','/'))
    return out
EXPORTS=native_exports()
def extract_functions(path,names,scope):
    tree=ast.parse(Path(path).read_text(encoding='utf-8-sig'))
    tree.body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in names]
    exec(compile(tree,str(path),'exec'),scope)
    return scope
scope=dict(np=np,safe_poly=ag.safe_poly,Polygon=Polygon,unary_union=unary_union,xy=ag.xy)
smooth_pavement=extract_functions(OLD/'route_common.py',{'smooth_pavement'},scope)['smooth_pavement']
def apt_line(points,name,style=51):
    out=['120 '+name]
    for i,p in enumerate(points):
        lo,la=ag.ll(*p);end=i==len(points)-1
        out.append(f'{115 if end else 111} {la:.9f} {lo:.9f}'+('' if end else f' {style}'))
    return out
def facade(resource,points,walls,height=15,name=''):
    return dict(resource=resource,points=[list(p) for p in points],walls=list(walls),height=height,name=name)
def facade_rows(item,index):
    out=[f'BEGIN_POLYGON {index} {item["height"]} 3','BEGIN_WINDING']
    for p,w in zip(item['points'],item['walls']):
        lo,la=ag.ll(*p);out.append(f'POLYGON_POINT {lo:.9f} {la:.9f} {w}')
    return out+['END_WINDING','END_POLYGON']
def aircraft_outline(pos,heading,length=56.7,span=35.8):
    # Conservative occupied silhouette; position is apt.dat aircraft reference.
    p=np.array(pos);f=np.array([math.sin(math.radians(heading)),math.cos(math.radians(heading))]);r=np.array([f[1],-f[0]])
    v=[(0,.48*length),(2,.43*length),(2,.04*length),(span/2,-.14*length),(span/2,-.23*length),(2,-.08*length),(2,-.35*length),(7,-.43*length),(7,-.48*length),(0,-.44*length),(-7,-.48*length),(-7,-.43*length),(-2,-.35*length),(-2,-.08*length),(-span/2,-.23*length),(-span/2,-.14*length),(-2,.04*length),(-2,.43*length)]
    return Polygon([p+r*x+f*y for x,y in v])
