from build_native import *
from collections import defaultdict
def validate():
    report={'checks':[],'warnings':[]};checks=report['checks'];apt=parse_apt(PACK/'Earth nav data/apt.dat');plan=build_plan()
    def check(name,ok,detail):checks.append({'name':name,'passed':bool(ok),'detail':detail})
    ramps=[a for a in apt if a['code']==1300];names=[r['name'] for r in ramps]
    check('Unique ramp names',len(names)==len(set(names)),len(names))
    check('Five charted runways',len([a for a in apt if a['code']==100])==5,'08L/26R, 08R/26L, 09/27, 15L/33R, 15R/33L')
    check('Charted runway width',all(a['parts'][1]=='45.72' for a in apt if a['code']==100),'150 ft / 45.72m')
    nodes={a['id']:a for a in apt if a['code']==1201};edges=[a for a in apt if a['code'] in (1202,1206)];used=set()
    for e in edges:used.update(map(int,e['parts'][1:3]))
    check('Routing references and orphans',set(nodes)==used,{'nodes':len(nodes),'edges':len(edges)})
    check('Contiguous node IDs',sorted(nodes)==list(range(len(nodes))),len(nodes))
    graph=defaultdict(set);runway_nodes=set()
    for e in edges:
        if e['code']!=1202:continue
        s=e['parts'];a,b=map(int,s[1:3]);graph[a].add(b);graph[b].add(a)
        if s[4]=='runway':runway_nodes.update((a,b))
    reachable=set(runway_nodes);stack=list(runway_nodes)
    while stack:
        a=stack.pop()
        for b in graph[a]-reachable:reachable.add(b);stack.append(b)
    new_edges=[e for e in edges if e['code']==1202 and e['parts'][-1]=='Apron']
    check('New apron links reach runway graph',all(int(e['parts'][1]) in reachable for e in new_edges),{'apron_edges':len(new_edges),'runway_reachable_nodes':len(reachable)})
    # Check new primary placements against each other and modeled building geometry.
    primary=[r for r in plan['new'] if not r.get('alternative')]+plan['details'];solids=unary_union([m['geom'] for m in plan['models'].values()]);conflicts=[]
    for i,r in enumerate(primary):
        g=aircraft_outline(r['pos'],r['heading'],r['size'])
        if g.intersection(solids).area>.05:conflicts.append(r['name']+' vs terminal')
        if 'building' in r and g.intersection(r['building']).area>.05:conflicts.append(r['name']+' vs existing terminal')
        for q in primary[i+1:]:
            if g.intersection(aircraft_outline(q['pos'],q['heading'],q['size'])).area>.05:conflicts.append(r['name']+' vs '+q['name'])
        for q in plan['ramps']:
            if not q.get('old_name') or q['kind']=='misc' or q['name']=='Gate '+r['name'] or q['name'] in ['Gate '+v['name'] for v in plan['details']]:continue
            gg=aircraft_outline(q['geom'].coords[0],q['heading'],q.get('rampmeta',['1301','C'])[1])
            if gg.intersection(g).area>.05:conflicts.append(r['name']+' vs '+q['name'])
    check('New and adjusted primary modeled aircraft envelopes',not conflicts,conflicts or f'{len(primary)} primary placements; no overlaps with new buildings or retained primary stands')
    jws=[a for a in apt if a['code']==1500];bad=[]
    for a in jws:
        s=a['parts'];size=int(s[5]);length=float(s[7]);d=(float(s[3])-float(s[8]))%360;lo,hi=[(11,23),(14,29),(17,38),(20,47)][size]
        if not(lo<=length<=hi and 0<=d<=90):bad.append(s)
    check('Jetway definitions',len(jws)==32 and not bad,{'count':len(jws),'invalid':bad})
    final_dsf=parse_dsf(ROOT/'generated/+29-096.txt')
    from r02_details import stale_west_barrier
    check('Reopened 15L corridor barricades removed',not any(stale_west_barrier(e) for e in final_dsf['entities']),{'original':sum(stale_west_barrier(e) for e in plan['dsf']['entities']),'remaining':sum(stale_west_barrier(e) for e in final_dsf['entities'])})
    west_names=['WA','WB','WG','WH','WJ','WK','WL','WM','WN']
    counts={n:len([e for e in edges if e['code']==1202 and e.get('name')==n]) for n in west_names}
    original={n:len([e for e in plan['apt'] if e['code']==1202 and e.get('name')==n]) for n in west_names}
    check('West taxiway routes retained and connected',counts==original and all(int(e['parts'][1]) in reachable and int(e['parts'][2]) in reachable for e in edges if e['code']==1202 and e.get('name') in west_names),counts)
    check('Current EA construction closure excluded from AI routing',not any(e.get('name')=='EA' for e in edges if e['code']==1202),'Three EA edges removed; NB and EE retained')
    check('Gate reconciliation', 'Gate A20' in names and 'Gate C29' not in names and 'Gate E6' not in names, 'A20 added; C29/E6 handled explicitly as directory/apron discrepancies, without speculative spawns')
    check('Overlapping E wide-body variants manual only',all(r['kind']=='misc' for r in ramps if r['name'] in ('Gate E2 wide','Gate E20 wide')),'E2 wide and E20 wide')
    # Resolve virtual resources through the actual installed X-Plane libraries, without modifying them.
    libmap={};root=pathlib.Path('X:/X-Plane 12/Resources/default scenery')
    for lib in root.rglob('library.txt'):
        for line in lib.read_text(errors='replace').splitlines():
            s=line.split()
            if len(s)>=3 and s[0] in ('EXPORT','EXPORT_BACKUP','EXPORT_EXTEND','EXPORT_EXCLUDE'):
                v=s[1];real=' '.join(s[2:]);libmap.setdefault(v.lower(),[]).append(lib.parent/real)
            if len(s)>=4 and s[0] in ('EXPORT_SEASON','EXPORT_RATIO'):
                v=s[2];real=' '.join(s[3:]);libmap.setdefault(v.lower(),[]).append(lib.parent/real)
    defs=[]
    for path in [ROOT/'generated/+29-096.txt',ROOT/'generated/+30-096.txt']:
        d=parse_dsf(path);defs+=d['objects']+d['polygons']
    missing=[]
    for ref in sorted(set(defs)):
        found=(PACK/ref).exists() or any(p.exists() for p in libmap.get(ref.lower(),[]))
        if not found:missing.append(ref)
    check('Scenery resources resolve',not missing,{'references':len(set(defs)),'missing':missing})
    obj_stats=[];bad=[]
    for obj in (PACK/'objects').glob('*.obj'):
        vertices=[];indices=[];decl=None;tris=[]
        for line in obj.read_text().splitlines():
            s=line.split()
            if not s:continue
            if s[0]=='VT':vertices.append([float(v) for v in s[1:]])
            if s[0] in ('IDX','IDX10'):indices+=list(map(int,s[1:]))
            if s[0]=='POINT_COUNTS':decl=list(map(int,s[1:]))
            if s[0]=='TRIS':tris.append(tuple(map(int,s[1:])))
        okay=decl is not None and decl[0]==len(vertices) and decl[3]==len(indices) and all(0<=i<len(vertices) for i in indices) and all(off+count<=len(indices) and count%3==0 for off,count in tris)
        if not okay:bad.append(obj.name)
        obj_stats.append({'name':obj.name,'vertices':len(vertices),'triangles':len(indices)//3})
    check('Custom OBJ8 tables',not bad,{'models':len(obj_stats),'triangles':sum(o['triangles'] for o in obj_stats),'invalid':bad})
    # Round-trip the compiled file, comparing its decoded geometry counts.
    compiled=PACK/'Earth nav data/+20-100/+29-096.dsf';roundtrip=ROOT/'generated/roundtrip.txt'
    result=subprocess.run([str(ROOT/'xptools-24-5/tools/DSFTool.exe'),'--dsf2text',str(compiled),str(roundtrip)],capture_output=True,text=True);result.check_returncode()
    a=parse_dsf(ROOT/'generated/+29-096.txt');b=parse_dsf(roundtrip)
    check('Compiled DSF round-trip',len(a['entities'])==len(b['entities']) and a['objects']==b['objects'] and a['polygons']==b['polygons'],{'entities':len(b['entities']),'object_resources':len(b['objects']),'polygon_resources':len(b['polygons'])})
    result=subprocess.run([str(ROOT/'xptools-24-5/tools/DSFTool.exe'),'--dsf2text',str(PACK/'Earth nav data/+30-100/+30-096.dsf'),str(ROOT/'generated/roundtrip-north.txt')],capture_output=True,text=True);result.check_returncode()
    na=parse_dsf(ROOT/'generated/+30-096.txt');nb=parse_dsf(ROOT/'generated/roundtrip-north.txt')
    check('North DSF closure placement round-trip',len(na['entities'])==len(nb['entities']) and na['objects']==nb['objects'],len(nb['entities']))
    native_bbox_errors=[]
    for item in json.loads((ROOT/'generated/scene.json').read_text())['models']:
        if not item['vertices']:native_bbox_errors.append(item['path'])
    check('Nonempty custom models',not native_bbox_errors,native_bbox_errors)
    report['warnings']=['Offline build only: no X-Plane load, jetway docking, AI taxi or night-light acceptance yet.','Building heights, roof equipment, new stop points and added apron details are modeled; current map outlines are not a surveyed as-built apron drawing.','C29 and E6 remain public-directory labels; checked apron evidence supports no independent active aircraft stand. Changes after the 2025 aerial capture are not ruled out.','Surrounding Gateway cargo, GA, maintenance, roads and existing terminals remain the detailed native baseline. Offline renders simplify existing library assets.','The long-running EA closure is encoded for this dated snapshot; short-duration daily NOTAMs are not simulated.']
    report['passed']=all(c['passed'] for c in checks);(ROOT/'generated/validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
    return report
if __name__=='__main__':validate()
