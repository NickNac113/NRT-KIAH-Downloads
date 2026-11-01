"""Refine B North in an isolated cumulative package. Never install or publish."""
from common import *
import shutil,subprocess,re
FACADES=[];CHANGES=[];TAXI=[]
def terminal():
    # Separate logical concourses, with identical anchors on each stacked layer.
    parts=[('West finger',B.intersection(box(-700,416,-375,650))),
           ('East finger',B.intersection(box(-375,416,0,650))),
           ('Head house',B.intersection(box(-700,300,0,416)))]
    for name,p in parts:
        p=p.simplify(.15,preserve_topology=True)
        pts=list(orient(p,sign=1).exterior.coords)[:-1]
        # First edge is the longest N/S wall, establishing sensible roof grain.
        k=max(range(len(pts)),key=lambda i:abs(pts[(i+1)%len(pts)][1]-pts[i][1]))
        pts=pts[k:]+pts[:k]
        upper=[];ground=[]
        for a,c in zip(pts,pts[1:]+pts[:1]):
            midpoint=Point(np.mean([a,c],axis=0));length=math.dist(a,c)
            internal=B.boundary.distance(midpoint)>.5
            upper.append(0 if internal else 6 if length>5 else 1)
            ground.append(0 if internal else 9 if length>5 else 0)
        FACADES.append(facade(KIT+'term_building_Ground_01.fac',pts,ground,5,name+' ground'))
        FACADES.append(facade(KIT+'term_building_Levels_02.fac',pts,upper,15,name+' upper'))
        if 'finger' in name:
            x=p.centroid.x
            equipment=[(x-8,445),(x-8,490),(x-8,535)]
            skylights=[[(x+7,445),(x+7,475)],[(x+7,505),(x+7,535)]]
        else:
            equipment=[(-550,365),(-492,366),(-435,358),(-375,362),(-315,358),(-245,366)]
            skylights=[[(-447,375),(-416,375)],[(-346,375),(-315,375)]]
        for i,(x,y) in enumerate(equipment):
            assert p.buffer(-4).covers(Point(x,y)),(name,x,y)
            FACADES.append(facade(KIT+'term_roof_elements_01.fac',pts[:2]+[(x,y-2),(x,y+2)],[0,0,5,0],15,name+f' HVAC {i+1}'))
        for i,line in enumerate(skylights):
            assert p.buffer(-3).covers(LineString(line)),(name,line)
            FACADES.append(facade(KIT+'term_roof_long_skylight_01.fac',pts[:2]+line,[0,0,4,0],15,name+f' skylight {i+1}'))
    CHANGES.append(dict(change='Replace custom B shell with stock terminal kit',module_count=3,footprint_max_change_m=.15,upper_roof_m=14.2))

def bridges():
    # Preserve the exact jetway roots and pillars. Only the fixed
    # tunnel skins are replaced with the same native glass bridge kit as C.
    for q in DSF['entities']:
        res=q['resource']
        if q['kind']!='object' or not re.fullmatch(r'objects/bridge_B(?:[1-9]|1[0-9]|2[0-3])\.obj',res):continue
        rows=(PREV/res).read_text().splitlines()
        verts=np.array([list(map(float,r.split()[1:])) for r in rows if r.startswith('VT ')])
        indices=[int(a) for r in rows if r.startswith(('IDX ','IDX10 ')) for a in r.split()[1:]]
        # Original authored tunnel vertices precede the support pillar. HF06
        # appended a circular pivot connector; retain that entire repair.
        first_support=next(i for i,v in enumerate(verts) if v[1]<4.2999)
        assert first_support>=24 and np.all((verts[:first_support,1]>=4.2999)&(verts[:first_support,1]<=7.2001))
        # Four sign vertices follow the original 22-vertex support box.
        # Lift the placard clear of the native tunnel's 8.01 m roof.
        sign_start=first_support+22
        assert set(np.round(verts[sign_start:sign_start+4,1],2))=={7.2,9.0}
        keep=[];skin=[]
        for i in range(0,len(indices),3):
            ids=indices[i:i+3];v=verts[ids]
            if max(ids)<first_support:
                skin.extend(ids)
            else:keep+=ids
        assert skin and keep
        v=verts[skin];o=np.array(q['geom'].coords[0]);en=v[:,[0,2]]*np.array([1,-1])+o
        hull=MultiPoint(en).convex_hull.simplify(.001)
        pts=list(orient(hull,sign=1).exterior.coords)[:-1]
        assert len(pts)==4,(res,len(pts))
        FACADES.append(facade(KIT+'term_bridge_01.fac',pts,[1]*4,10,Path(res).stem))
        out=[];commands=[];data_done=False;vertex_index=0
        for r in rows:
            if r.startswith('VT '):
                if sign_start<=vertex_index<sign_start+4:
                    s=r.split();s[2]=f'{float(s[2])+1.1:.6f}';r=' '.join(s)
                out.append(r);vertex_index+=1
            elif r.startswith('POINT_COUNTS '):
                s=r.split();s[-1]=str(len(keep));out.append(' '.join(s))
            elif r.startswith(('IDX ','IDX10 ')):data_done=True
            elif r.startswith('TRIS '):continue
            elif data_done:commands.append(r)
            else:out.append(r)
        out+=['IDX '+str(i) for i in keep]+commands+[f'TRIS 0 {len(keep)}']
        # IDX tables must precede drawing commands; the input has only global
        # state directives and a single TRIS draw, so the rebuilt table is valid.
        (PACK/res).write_text('\n'.join(out)+'\n')
        CHANGES.append(dict(change='Native fixed tunnel; retained pillar and pivot connector; raised gate sign 1.1 m',resource=res))

def bezier(p0,p1,p2,p3,name):
    # apt handles point toward the following node. Last incoming control is reflected.
    lo,la=ag.ll(*p0);ho,ha=ag.ll(*p1)
    qo,qa=ag.ll(*p3);jh=np.array(p3)*2-np.array(p2);jo,ja=ag.ll(*jh)
    return ['120 '+name,f'112 {la:.9f} {lo:.9f} {ha:.9f} {ho:.9f} 51',f'116 {qa:.9f} {qo:.9f} {ja:.9f} {jo:.9f}']

def paint_and_network():
    replaced=[];removed=[];output=[]
    remove_pairs={frozenset((855,329)),frozenset((329,326)),frozenset((859,112))}
    for q in APT:
        header=q['lines'][0]
        if q['code']==1201 and q['id'] in (855,859):
            # These two nodes belonged only to the obsolete parallel branches.
            uses=[a for a in APT if a['code']==1202 and q['id'] in (a['start'],a['end'])]
            assert all(frozenset((a['start'],a['end'])) in remove_pairs for a in uses)
            removed.append(header);continue
        if q['code']==120 and header in ('120 R03 aircraft circulation 105','120 R03 aircraft circulation 107'):
            removed.append(header);continue
        if q['code']==120 and header=='120 HF06 B North arrival curve':
            start=NODES[1451];end=NODES[1450];k=.55228475
            output+=bezier(start,(start[0]+30*k,start[1]),(end[0],end[1]+30*k),end,'R28 B North R1 arrival')
            replaced.append(header);continue
        if q['code']==120 and header=='120 HF06 B North departure curve':
            start=NODES[1450];end=NODES[1452];k=.55228475
            output+=bezier(start,(start[0],start[1]+30*k),(end[0]-30*k,end[1]),end,'R28 B North R1 departure')
            replaced.append(header);continue
        if q['code']==120 and header.startswith('120 HF04 preserved outer edge') and q.get('geom') is not None and B.buffer(.3).covers(q['geom']):
            removed.append(header);continue
        if q['code']==1202:
            p=q['parts'];pair=frozenset(map(int,p[1:3]))
            if pair in remove_pairs:removed.append(header);continue
            # Name the retained B-side NG route; preserve its geometry and size.
            if pair in {frozenset(z) for z in [(112,109),(109,110),(110,14),(14,111)]}:
                output.append(' '.join(p[:5]+['NG']));replaced.append(header);continue
        output+=q['lines'] if q['code']!=99 else []
    nd=[NODES[i] for i in [125,130,129,128,127,126,315,325,326]]
    ng=[NODES[i] for i in [111,14,110,109,112]]
    output+=apt_line(nd,'R28 B North ND - matched to retained aircraft network')
    output+=apt_line(ng,'R28 B North NG - matched to retained aircraft network')
    # Parallel C-side guidance is retained as context, not an extra B lane.
    TAXI.extend([dict(name='ND',points=nd),dict(name='R1',points=[NODES[856],NODES[1450]]),dict(name='NG',points=ng)])
    (PACK/'Earth nav data/apt.dat').write_text('\n'.join(output+['99'])+'\n')
    CHANGES.append(dict(change='Taxi guidance consolidation',removed=removed,replaced=replaced))

def build_dsf():
    raw=DSF_SOURCE.read_text();q=next(q for q in DSF['entities'] if q['resource']=='objects/B_North.obj')
    block='\n'.join(q['lines']);assert raw.count(block)==1
    raw=raw.replace(block,'# R28 B North replaced by native terminal facades')
    defs=list(DSF['polygons']);added=[]
    for f in FACADES:
        if f['resource'] not in defs:
            defs.append(f['resource']);added.append('POLYGON_DEF '+f['resource'])
    first=raw.index('FILTER ')
    raw=raw[:first]+'\n'.join(added)+'\n'+raw[first:]
    new=['FILTER 0']
    for f in FACADES:new+=facade_rows(f,defs.index(f['resource']))
    raw+='\n'+'\n'.join(new)+'\n'
    textpath=ROOT/'qa/R28_DSF.txt';textpath.write_text(raw)
    target=PACK/'Earth nav data/+20-100/+29-096.dsf'
    tool=OLD/'xptools-24-5/tools/DSFTool.exe'
    results=[]
    for args in [['--text2dsf',str(textpath),str(target)],['--dsf2text',str(target),str(ROOT/'qa/R28_Roundtrip.txt')]]:
        run=subprocess.run([str(tool),*args],capture_output=True,text=True,check=True);results.append(run.stdout+run.stderr)
    (ROOT/'qa/DSF_Compile.txt').write_text('\n'.join(results))

def main():
    assert not (ROOT/'NRT_KIAH_R28_Review.zip').exists(),'Sealed revision; use a successor.'
    for d in ['package','qa','output','reference']:(ROOT/d).mkdir(exist_ok=True)
    record=ROOT/'reference/R27_Hashes.json';snap=snapshot(PREV)
    if record.exists():assert json.loads(record.read_text())==snap,'R27 changed'
    else:record.write_text(json.dumps(snap,indent=2))
    shutil.copytree(PREV,PACK,dirs_exist_ok=True)
    terminal();bridges();paint_and_network();build_dsf()
    evidence=dict(revision='R28',baseline='R27',status='offline review - not installed or published',facades=FACADES,changes=CHANGES,taxi=TAXI)
    (ROOT/'qa/R28_Evidence.json').write_text(json.dumps(evidence,indent=2))
    (PACK/'R28_Changes.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(dict(package=str(PACK),facades=len(FACADES),changes=len(CHANGES)),indent=2))
if __name__=='__main__':main()
