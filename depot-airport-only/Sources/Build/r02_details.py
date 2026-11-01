from native_mesh import *

def stale_west_barrier(e):
    if e['kind']!='object' or not e['resource'].endswith('/Barriers/concrete/red_3m.obj'):return False
    lon,lat=e['coords'][:2]
    return -95.353<lon<-95.337 and 29.959<lat<29.983

def scenery_detail_cleanup(e,plan):
    # Replace the three C connector jetways affected by the R01 gate moves.
    if 'Jetway' in e['resource']:
        return any(e['geom'].distance(Point(r['door']))<36 for r in plan['details'] if r['name'].startswith('C'))
    if e['kind']=='object' and any(s in e['resource'] for s in ('Ramp_Equipment/','vehicles/','Vehicles/','Barriers/')):
        return any(e['geom'].distance(aircraft_outline(r['pos'],r['heading'],r['size']))<3 for r in plan['details'])
    return False

def equipment_and_lights(plan):
    stands=[r for r in plan['new'] if not r.get('alternative')]+plan['details']
    planes=unary_union([aircraft_outline(r['geom'].coords[0],r['heading'],r.get('rampmeta',['1301','C'])[1]) for r in plan['ramps'] if r['kind']!='misc'])
    buildings=unary_union([v['geom'] for v in plan['models'].values()]+[plan['buildings']['iah-ta-2'],plan['buildings']['iah-tc-2']])
    pave=unary_union([a['geom'] for a in plan['apt'] if a['code']==110]+[plan['zones']['B_North'],plan['zones']['D_West']])
    items=[];pads=[]
    resources=['lib/airport/Ramp_Equipment/GPU_1.obj','lib/airport/Ramp_Equipment/Luggage_Cart_1.obj','lib/airport/Ramp_Equipment/Tow_Tractor_1.obj']
    occupied=[]
    for i,r in enumerate(stands):
        p=np.array(r['pos']);f=heading_vec(r['heading']);right=np.array([f[1],-f[0]])
        for side in (-1,1):
            center=p+right*side*12+f*5
            pad=Polygon([center+right*x+f*y for x,y in [(-3,-4),(3,-4),(3,4),(-3,4)]])
            if buildings.intersects(pad.buffer(1)) or planes.intersects(pad.buffer(2)) or not pave.covers(pad):continue
            if any(pad.distance(q)<2 for q in occupied):continue
            occupied.append(pad);pads.append({'name':r['name'],'geom':pad})
            for j,resource in enumerate(resources[:2]):
                pt=center+f*(j*3-1.5);items.append({'resource':resource,'pos':pt.tolist(),'heading':r['heading'],'purpose':'modeled service equipment '+r['name']})
            break
    # Lights are placed beside the terminal wall, clear of stands, at selected actual gate bays.
    for i,r in enumerate(stands):
        if i%3:continue
        f=heading_vec(r['heading']);right=np.array([f[1],-f[0]]);door=np.array(r['door'])
        for distance in (16,22,-16,-22):
            pt=door-f*5+right*distance
            if buildings.buffer(1.5).contains(Point(pt)) or planes.buffer(6).contains(Point(pt)) or not pave.covers(Point(pt)):continue
            items.append({'resource':'lib/airport/Common_Elements/Lighting/Dir_Ramp_Lit_Med.obj','pos':pt.tolist(),'heading':(r['heading']+180)%360,'purpose':'modeled apron floodlight'});break
    return items,pads

def ea_barriers():
    # Current RON works close EA between NB and EE; rows sit off the junctions.
    out=[]
    for lat in (29.99105,30.00065):
        x,y=xy(-95.313975,lat)
        for dx in range(-15,16,3):out.append({'resource':'lib/airport/Common_Elements/Barriers/concrete/red_3m.obj','pos':[x+dx,y],'heading':90,'purpose':'EA current closure'})
    return out
