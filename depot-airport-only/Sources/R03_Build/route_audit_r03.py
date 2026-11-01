from route_common import *
import csv,hashlib
from check_airport_structure import check_structure

def audit():
    apt=parse_apt(TARGET/'Earth nav data/apt.dat');nodes,edges=network(apt);ctx=scene_context(apt)
    report={'checks':[],'notes':[]};checks=report['checks']
    def check(name,ok,detail):checks.append(dict(name=name,passed=bool(ok),detail=detail))
    structure=check_structure(TARGET/'Earth nav data/apt.dat')
    check('Native airport declaration owns all KIAH data',structure['passed'],structure)
    used={e[k] for e in edges for k in ('a','b')}
    check('Every route node referenced; IDs unique and contiguous',set(nodes)==used and sorted(nodes)==list(range(len(nodes))),len(nodes))
    check('Directions and aircraft size codes valid',all(e['direction'] in ('oneway','twoway') and (e['code']==1206 or e['kind']=='runway' or e['kind'][-1].upper() in SPAN) for e in edges),len(edges))
    check('No zero-length route segments',all(line(e,nodes).length>.025 for e in edges),len(edges))
    for code,label in [(1202,'Aircraft'),(1206,'Service')]:
        crosses=crossing_pairs(edges,nodes,code)
        check(label+' intersections share junction nodes',not crosses,[dict(a=a['old_index'],b=b['old_index'],location=list(p.centroid.coords[0])) for a,b,p in crosses])
        g=adjacency(edges,code,undirected=True);comps=components(g)
        report[label.lower()+'_components']=[len(c) for c in comps]
        if code==1202:check('One connected aircraft network',len(comps)==1,[len(c) for c in comps])
    runways=ctx['runways'];rwids={end for r in runways for end in r['name'].split('/')}
    flowends={a['parts'][1] for a in apt if a['code'] in (1100,1110)}
    check('All flow runway identifiers exist',flowends<=rwids,sorted(flowends))
    rw_edges=[e for e in edges if e['code']==1202 and e['kind']=='runway']
    check('All five runways have taxi routes',{e['name'] for e in rw_edges}=={r['name'] for r in runways},Counter(e['name'] for e in rw_edges))
    runway_bad=[];runway_coverage=[]
    for r in runways:
        es=[e for e in rw_edges if e['name']==r['name']];gs=[line(e,nodes) for e in es]
        s=r['parts'];center=LineString([xy(float(s[10]),float(s[9])),xy(float(s[19]),float(s[18]))])
        if not gs:continue
        offsets=[max(center.distance(Point(c)) for c in g.coords) for g in gs]
        if max(offsets)>1.5 or any(not r['geom'].buffer(2).covers(g) for g in gs):runway_bad.append(r['name'])
        coverage=(max(center.project(Point(c)) for g in gs for c in g.coords)-min(center.project(Point(c)) for g in gs for c in g.coords))/center.length
        runway_coverage.append(dict(runway=r['name'],coverage_percent=round(coverage*100,2),max_centerline_offset_m=round(max(offsets),3)))
    check('Runway routes within pavement and on centerlines',not runway_bad,runway_bad or runway_coverage)
    check('Runway route spans cover at least 95 percent of each runway',all(r['coverage_percent']>=95 for r in runway_coverage),runway_coverage)
    seeds={e[k] for e in rw_edges for k in ('a','b')}
    g=adjacency(edges,1202);back=adjacency(edges,1202,reverse=True)
    f=reachable(g,seeds);b=reachable(back,seeds)
    check('All aircraft route nodes can reach and be reached from a runway',set(g)<=f&b,dict(nodes=len(g),cannot_depart=sorted(set(g)-b),cannot_arrive=sorted(set(g)-f)))
    paved=unary_union([ctx['pavement']]+[e['geom'] for e in ctx['entities'] if e['kind']=='polygon' and '/pavement/' in e['resource'] and e['geom'].area>0]).buffer(1)
    pavedprep=prep(paved);solids=ctx['solids'];plane_union=unary_union([p['geom'] for p in ctx['planes']]);obstacles=unary_union([solids,plane_union])
    air_rows=[];hot_flags=[]
    for e in edges:
        if e['code']!=1202:continue
        geo=line(e,nodes);off=0 if pavedprep.covers(geo) else geo.difference(paved).length
        building=geo.intersection(solids).length if geo.intersects(solids) else 0
        clearance=geo.distance(obstacles);width=SPAN.get(e['kind'][-1].upper(),0) if e['kind']!='runway' else 0
        air_rows.append(dict(segment=e['old_index'],name=e['name'],direction=e['direction'],class_code=e['kind'],length_m=round(geo.length,3),off_pavement_m=round(off,3),building_intersection_m=round(building,3),modeled_obstacle_clearance_m=round(clearance,3),required_clearance_m=width/2+2 if width else 0,start_node=e['a'],end_node=e['b']))
        for r in runways:
            if e['kind']=='runway' and e['name']==r['name']:continue
            if not geo.intersects(r['geom'].buffer(45)):continue
            tags=defaultdict(set)
            for attr in e['attrs']:
                ss=attr.split()
                if ss[0]=='1204':tags[ss[1]].update(ss[2].split(','))
            if not set(r['name'].split('/'))<=tags['arrival'] or not set(r['name'].split('/'))<=tags['departure']:
                hot_flags.append(dict(edge=e['old_index'],runway=r['name'],name=e['name'],attrs=e['attrs'],location=list(geo.centroid.coords[0])))
    check('All aircraft centerlines on modeled pavement',not any(r['off_pavement_m']>2 for r in air_rows),[r for r in air_rows if r['off_pavement_m']>2])
    check('All aircraft centerlines clear represented buildings',not any(r['building_intersection_m']>.1 for r in air_rows),[r for r in air_rows if r['building_intersection_m']>.1])
    check('Aircraft widths respect modeled parked-aircraft and building clearance',all(r['modeled_obstacle_clearance_m']+.12>=r['required_clearance_m'] for r in air_rows),[r for r in air_rows if r['modeled_obstacle_clearance_m']+.12<r['required_clearance_m']])
    check('Runway-proximity route segments carry arrival and departure protection',not hot_flags,hot_flags)
    check('All preserved hot-zone references name actual runway ends',all(set(s.split()[2].split(','))<=rwids for e in edges for s in e['attrs'] if s.startswith('1204 ')),'Every 1204 record checked')
    # Access is to the adjacent taxi network, not a taxi edge drawn into the parking stand.
    def can_join(e,from_runway,to_runway):
        if e['direction']=='oneway':
            return e['a'] in from_runway and e['b'] in to_runway
        return any(e[k] in from_runway for k in ('a','b')) and any(e[k] in to_runway for k in ('a','b'))
    ramp_rows=[]
    for size in SPAN:
        g=adjacency(edges,1202,size);back=adjacency(edges,1202,size,reverse=True);fromrw=reachable(g,seeds);torw=reachable(back,seeds)
        runway_access={r['name']:(reachable(g,{e[k] for e in rw_edges if e['name']==r['name'] for k in ('a','b')}),reachable(back,{e[k] for e in rw_edges if e['name']==r['name'] for k in ('a','b')})) for r in runways}
        candidates=[e for e in edges if e['code']==1202 and e['kind']!='runway' and allowed(e,size) and all(can_join(e,fr,to) for fr,to in runway_access.values())]
        for ramp in ctx['ramps']:
            if ramp.get('rampmeta',['1301','C'])[1]!=size:continue
            ordered=sorted(candidates,key=lambda e:line(e,nodes).distance(ramp['geom']))
            # Require the last approach to avoid terminal walls; final maneuver path remains simulator generated.
            interiors=[d['geom'] for d in ctx['entities'] if '/hangars/' in d['resource'] and '/interior_' in d['resource'] and d['geom'].covers(ramp['geom'])]
            access_solids=solids.difference(unary_union(interiors)) if interiors else solids
            viable=[e for e in ordered[:30] if not LineString([ramp['geom'].coords[0],line(e,nodes).interpolate(line(e,nodes).project(ramp['geom'])).coords[0]]).intersects(access_solids)]
            e=viable[0] if viable else (ordered[0] if ordered else None)
            names=[n for n,(fr,to) in runway_access.items() if e and can_join(e,fr,to)]
            ramp_rows.append(dict(ramp=ramp['name'],kind=ramp['kind'],size=size,access_segment=e['old_index'] if e else None,distance_m=round(line(e,nodes).distance(ramp['geom']),2) if e else None,clear_terminal_approach=bool(viable),runways_reachable_both_directions=';'.join(names),runway_count=len(names),note='Starts inside hangar interior; door clearance requires simulator check' if interiors else ('Manual alternative: final maneuver and neighboring stand occupancy require review' if ramp['kind']=='misc' else '')))
    check('Every ramp has a size-compatible adjacent network with paths to all five runways',all(r['runway_count']==5 and r['distance_m'] is not None and r['clear_terminal_approach'] for r in ramp_rows),[r for r in ramp_rows if r['runway_count']<5 or r['distance_m'] is None or not r['clear_terminal_approach']])
    check('Every automatic aircraft stand has network access within 250 metres',all(r['distance_m'] is not None and r['distance_m']<250 for r in ramp_rows if r['kind']!='misc'),dict(automatic_stands=sum(r['kind']!='misc' for r in ramp_rows),maximum_distance_m=max(r['distance_m'] for r in ramp_rows if r['kind']!='misc')))
    report['manual_access_review']=[r for r in ramp_rows if r['kind']=='misc' and r['distance_m']>=250]
    report['hangar_interior_review']=[r for r in ramp_rows if r['note'].startswith('Starts inside')]
    build=json.loads((R03/'build-report.json').read_text());truck_edges=[e for e in edges if e['code']==1206]
    tg=adjacency(edges,1206);tback=adjacency(edges,1206,reverse=True);service_rows=[]
    def entry_nodes(e):return [e['a'],e['b']] if e['direction']=='twoway' else [e['a']]
    def exit_nodes(e):return [e['a'],e['b']] if e['direction']=='twoway' else [e['b']]
    for t in build['targets']:
        p=Point(t['point']);e=min(truck_edges,key=lambda e:line(e,nodes).distance(p));fromtarget=reachable(tg,exit_nodes(e));totarget=reachable(tback,entry_nodes(e))
        types=set();depot_names=[]
        for a in apt:
            if a['code']!=1400:continue
            s=a['parts'];q=Point(xy(float(s[2]),float(s[1])));qe=min(truck_edges,key=lambda qedge:line(qedge,nodes).distance(q))
            if any(n in fromtarget for n in entry_nodes(qe)) and any(n in totarget for n in exit_nodes(qe)):types.add(s[4]);depot_names.append(' '.join(s[6:]))
        service_rows.append(dict(approach=t['name'],model=t['model'],route_distance_m=round(line(e,nodes).distance(p),3),vehicle_types=';'.join(sorted(types)),round_trip_depots=len(depot_names)))
    required={'baggage_train','baggage_loader','fuel_liners','food','gpu','pushback'}
    check('Every rebuilt stand service approach reaches all six service vehicle types and can return',all(required<=set(r['vehicle_types'].split(';')) and r['route_distance_m']<.1 for r in service_rows),service_rows)
    parks=[a for a in apt if a['code']==1400 and 'R03 ' in a['lines'][0]];dest=[a for a in apt if a['code']==1401 and 'R03 ' in a['lines'][0]]
    check('Moving service vehicle parking definitions present',len(parks)>=18,Counter(a['parts'][4] for a in parks))
    new_service=[e for e in truck_edges if e['name'].startswith(('Service ','Terminal service connector'))]
    fixed=[e['geom'].buffer(3.5) for e in ctx['entities'] if e['kind']=='object' and any(t in e['resource'] for t in ['Ramp_Equipment/','Barriers/','Lighting/'])]
    sob=unary_union([solids.buffer(3.9),plane_union.buffer(3.9),*fixed])
    check('New service routes clear modeled buildings, parked aircraft and fixed equipment',not any(line(e,nodes).intersects(sob) for e in new_service),[e['old_index'] for e in new_service if line(e,nodes).intersects(sob)])
    check('New service routes remain on modeled pavement',all(pavedprep.covers(line(e,nodes)) for e in new_service),len(new_service))
    keepout=unary_union([r['geom'].buffer(60) for r in runways])
    check('No service route crosses a runway protection area',not any(line(e,nodes).intersects(keepout) for e in truck_edges),[e['old_index'] for e in truck_edges if line(e,nodes).intersects(keepout)])
    truck_rows=[]
    parking_clearance=[]
    for a in parks+dest:
        s=a['parts'];q=Point(xy(float(s[2]),float(s[1])));e=min(truck_edges,key=lambda e:line(e,nodes).distance(q));near=line(e,nodes).interpolate(line(e,nodes).project(q));approach=LineString([q,near]);cc=reachable(tg,exit_nodes(e))&reachable(tback,entry_nodes(e))
        truck_rows.append(dict(name=' '.join(s[6:] if a['code']==1400 else s[5:]),code=a['code'],distance_m=round(q.distance(near),2),approach_clear=not approach.intersects(sob),bidirectional_service_component_nodes=len(cc),paved=pavedprep.covers(q)))
        foot=box(q.x-2.2,q.y-5.5,q.x+2.2,q.y+5.5)
        parking_clearance += [dict(parking=truck_rows[-1]['name'],edge=e['old_index']) for e in edges if e['code']==1202 and line(e,nodes).distance(foot)+.1<SPAN.get(e['kind'][-1].upper(),80)/2+2]
    check('New truck parking and destinations have clear, short access to a returnable service network',all(r['approach_clear'] and r['distance_m']<40 and r['bidirectional_service_component_nodes']>100 and r['paved'] for r in truck_rows),truck_rows)
    check('New parked service vehicles remain outside aircraft taxi wingspan clearance',not parking_clearance,parking_clearance)
    check('Replaced apron guidance paint follows the new paths',not any(a['code']==120 and '2026 apron circulation' in a['lines'][0] for a in apt) and sum(a['code']==120 and 'R03 aircraft circulation' in a['lines'][0] for a in apt)==6,'Five apron paths and the widebody connection updated')
    check('EA construction closure stays excluded from aircraft routing',not any(e['code']==1202 and e['name']=='EA' for e in edges),'No EA taxi edges')
    baseapt=parse_apt(BASE/'Earth nav data/apt.dat')
    check('All 240 ramp definitions and five runways preserved',[a['lines'] for a in apt if a['code'] in (100,1300)]==[a['lines'] for a in baseapt if a['code'] in (100,1300)],len(ctx['ramps']))
    changed_assets=[]
    for sub in ['objects','textures','Earth nav data/+20-100','Earth nav data/+30-100']:
        for f in (BASE/sub).rglob('*'):
            if f.is_file() and hashlib.sha256(f.read_bytes()).digest()!=hashlib.sha256((TARGET/f.relative_to(BASE)).read_bytes()).digest():changed_assets.append(str(f.relative_to(BASE)))
    check('Compiled scenery tiles, objects and textures unchanged from validated R02',not changed_assets,changed_assets or 'Only airport ground routing and vehicle starts/destinations modified')
    for name,rows in [('Aircraft_Route_Audit',air_rows),('Ramp_Access_Audit',ramp_rows),('Service_Stand_Coverage',service_rows),('Service_Depot_Access',truck_rows)]:
        with (R03/(name+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    report.update(passed=all(c['passed'] for c in checks),counts=dict(aircraft_segments=len(air_rows),service_segments=len(truck_edges),ramps=len(ramp_rows),service_approaches=len(service_rows),new_vehicle_parks=len(parks),new_destinations=len(dest)),runway_coverage=runway_coverage,notes=['Offline checks against modeled geometry and native routing definitions; no X-Plane runtime acceptance.','Service final docking and aircraft last-leg/pushback maneuvers are generated by X-Plane and aircraft-specific.','Manual C14 wide remains a conditional start: nearest connected class D route is 321 m away; no unsafe route was added through occupied neighboring stands. Simulator maneuver/occupancy review required.','United Maintenance 3 starts inside a hangar interior; the open doorway is not modeled as a solid obstacle for apron access. Check actual doorway clearance in the simulator.','Existing library object detail and terrain are not fully represented by the offline obstacle model.'])
    (R03/'validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'passed':report['passed'],'counts':report['counts'],'failures':[c for c in checks if not c['passed']]},indent=2))
    return report

if __name__=='__main__':audit()
