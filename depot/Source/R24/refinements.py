"""R24-specific build operations; seed_builder embeds these in build_r24.py."""
def parking_hangar():
    m=g.Mesh('r24_indoor_parking',[2473,359]);m.clockwise=True
    # Union each height band before extrusion: no intersecting wall solids or
    # coplanar end caps at the southwest/southeast corners.
    shell=union([box(2434,284,2435,433.3),box(2434,284,2512,285),box(2434,432.3,2512,433.3),box(2510,284,2512,290),box(2510,428,2512,433.3)])
    m.extrude(shell,0,16,0)
    m.extrude(shell.union(box(2510,290,2512,428)),16,20,0)
    g.block(m,[2434,284,2512,433.3],20,20.6,0,4)
    # A small construction gap to MH2 avoids the independently quantized
    # DSF placements creating another coplanar shared wall.
    for x in [2440,2462,2484,2507]:
        g.rod(m,[x,285,18.1],[x,432.3,18.1],.30,7)
        for y in np.arange(286,424,8):
            g.rod(m,[x,y,18.1],[x,y+4,19.85],.14,7);g.rod(m,[x,y+4,19.85],[x,y+8,18.1],.14,7)
    for x in [2447,2470,2493]:
        for y in [310,344,378,412]:g.block(m,[x-5,y-1.2,x+5,y+1.2],20.61,20.78,2,2)
    # Looking at the east facade, south is LEFT and north is RIGHT. Each half
    # has its own OpenSAM dataref and independent 12-leaf sliding pocket.
    for side,ref in [(-1,REF_LEFT),(1,REF_RIGHT)]:
        for j in range(12):
            ya,yb=sorted([359+side*j*5.75,359+side*(j+1)*5.75])
            target=284.05+j*.012 if side<0 else 427.4+j*.012
            delta=target-ya
            cmd=['ANIM_trans_begin '+ref,'ANIM_trans_key 0 0 0 0',f'ANIM_trans_key 1 {-j*.10:.6f} 0 {-delta:.6f}','ANIM_trans_end']
            def draw(ya=ya,yb=yb):
                g.block(m,[2510.8,ya,2511.05,yb],.05,15.95,1,1)
                g.block(m,[2511.065,ya+.10,2511.10,yb-.10],6,7.5,2,2)
            m.animated(cmd,draw)
    for y in [300,328,356,384,412]:m.flood(2508,y,18,0,0,9000)
    save(m)

def truck_doors_static():
    # Bake the existing authored open pose. No plugin refs remain on this OBJ.
    scope=dict(np=np,math=math,Image=Image)
    tr=ast.parse((g.LEGACY/'obj_reader.py').read_text())
    exec(compile(ast.Module(body=[n for n in tr.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'obj_reader','exec'),scope)
    rel='objects/nrt_test/r22_nrt_truck_doors.obj';rows=(OLD/rel).read_text().splitlines()
    refs=set(re.findall(r'nrt/kiah/[^\s]+','\n'.join(rows)))
    # Local EN coordinates are converted back to the OBJ8 local axes below.
    tris,uv,_=scope['readobj'](OLD/rel,[0,0],vals={r:1 for r in refs},full=True)
    verts=[]
    for tri,tex in zip(tris,uv):
        p=np.column_stack([tri[:,0],tri[:,2],-tri[:,1]])
        normal=np.cross(p[1]-p[0],p[2]-p[0]);normal/=max(np.linalg.norm(normal),1e-12)
        for v,t in zip(p,tex):verts.append([*v,*normal,*t])
    out=[r for r in rows if r.startswith(('TEXTURE','GLOBAL_'))]
    out=['I','800','OBJ',*out,f'POINT_COUNTS {len(verts)} 0 0 {len(verts)}']
    out+=['VT '+' '.join(f'{v:.6f}' for v in p) for p in verts]
    for i in range(0,len(verts),10):
        ids=list(range(i,min(i+10,len(verts))));out+=['IDX10 '+' '.join(map(str,ids))] if len(ids)==10 else ['IDX '+str(x) for x in ids]
    out+=['ATTR_no_cull',f'TRIS 0 {len(verts)}']
    (PACK/rel).write_text('\n'.join(out)+'\n')

def cleanup():
    # Original open parking square extends behind the new building. Clear its
    # entire footprint rather than merely hiding the part inside the hangar.
    region=box(2410,276,2513,434.2).union(box(2646,395,2707,449))
    for name in ['paint','ramp_safety','ramp_wear','taxi_wear']:
        g.cut_obj('objects/nrt_test/'+name+'.obj',region)
    # R23 removed the fabric, but the fence's steel frame belongs to another
    # mesh. Remove BOTH pieces from the former west car-park boundary.
    g.cut_obj('objects/nrt_test/landside_fence.obj',box(2680,275,2742,343))
    # Clip just fence metal in the mixed security mesh; keep its guardhouse,
    # entry barrier, CCTV and original entrance canopy.
    for region in [box(2719.6,276.5,2720.4,333.5),box(2725.7,276.5,2733.3,277.5)]:
        g.cut_obj('objects/nrt_test/landside_security.obj',region)
    paint_cleanup.extend(g.changes)

def pedestrian_and_ga():
    # Low, flush paint only around the helicopter. No beacon or new mast.
    p=g.Mesh('r24_access_paint',[2674,430],True);p.layer=('markings',5)
    walk=LineString(WALK)
    corridor=walk.buffer(.8,cap_style=2,join_style=2).union(LineString(GA_WALK).buffer(.8,cap_style=2,join_style=2))
    # White edge outline, intentionally unpainted center for natural pavement.
    p.flat(corridor.boundary.buffer(.065,cap_style=2,join_style=2),0,5)
    for center,heading in [([2690,374.5],90),([2721,403],0),([2702,451],270),([2693,448],180)]:
        # Small pedestrian pictograms, rather than a vehicle taxi stripe.
        f=g.direction(heading);r=np.array([f[1],-f[0]])
        def xy(x,y):return np.array(center)+r*x+f*y
        p.flat(Point(xy(0,.60)).buffer(.14,quad_segs=8),0,5)
        for pts in [[(0,.40),(0,-.25)],[(-.37,.12),(.37,.12)],[(0,-.25),(-.35,-.75)],[(0,-.25),(.35,-.75)]]:
            p.flat(LineString([xy(*q) for q in pts]).buffer(.055,cap_style=2),0,5)
    p.flat(LineString([(2673.6,454.3),(2676.4,454.3)]).buffer(.13,cap_style=2),0,4)
    p.flat(LineString([(2691.6,444.5),(2694.4,444.5)]).buffer(.10,cap_style=2),0,4)
    # East-facing GA start, with pedestrian access at the north bay edge.
    p.flat(GA_BOX.boundary.buffer(.065,join_style=2),0,5)
    f=g.direction(GA_HEAD);right=np.array([f[1],-f[0]])
    p.flat(LineString([np.array(GA_NG)-right*2,np.array(GA_NG)+right*2]).buffer(.10,cap_style=2),0,4)
    save(p)
    p=g.Mesh('r24_access_ids',[2674,430],True);p.texture='r24_ground_ids.png';p.normal=None
    for text,c,w,h,head in [('HELIPAD ACCESS',[2721,429],9,1.1,90),('HOLD / ROTORS',[2675,453],6,1,0),('MAX WINGSPAN 66 FT / 20 M',[2687,415.5],14,1.2,0)]:p.label(text,c,w,h,heading=head)
    save(p)
    # A flush airside pedestrian door at the north side of the headquarters
    # wing provides an actual destination for the marked helipad walkway.
    m=g.Mesh('r24_heli_access_door',[2674,365]);m.clockwise=True
    g.block(m,[2673.60,363.9,2673.78,366.1],.12,3.1,1,1)
    g.block(m,[2673.53,364.05,2673.60,365.95],.22,2.95,2,2)
    g.rod(m,[2673.48,365.0,1.0],[2673.48,365.0,1.65],.045,5)
    save(m)

def apt():
    out=[]
    for q in g.ag.parse_apt(OLD/'Earth nav data/apt.dat'):
        if q['code']==1300 and q['name']=='NRT CANOPY':continue
        if q['code']==120 and 'canopy detached side-entry' in q['lines'][0]:continue
        for line in q['lines']:
            if line.strip()=='99':continue
            out.append(line.replace('NRT PRIVATE HANGAR','NRT INDOOR PARKING'))
    for name,ng,head,size,types in [('NRT CANOPY',NG,180,'C','jets'),('NRT11',GA_NG,GA_HEAD,'B','props|turboprops|jets')]:
        lo,la=g.ag.ll(*ng);out+=[f'1300 {la:.9f} {lo:.9f} {head} gate {types} {name}',f'1301 {size} none']
    # Native apt.dat painted-line records (WED type 51). These are guidance,
    # not autonomous ground movements or a promise of BBJ2 turning clearance.
    for label,points in [('Canopy pull-through entry',PROPOSAL['arrival']),('Canopy pull-through exit',PROPOSAL['departure']),('NRT11 connected east-facing parking',GA_ROUTE)]:
        points=list(LineString(points).simplify(.025,preserve_topology=True).coords)
        out+=['120 NRT R24 '+label]
        for i,(x,y) in enumerate(points):
            lo,la=g.ag.ll(x,y);last=i==len(points)-1
            out+=[f'{115 if last else 111} {la:.9f} {lo:.9f}'+('' if last else ' 51')]
    out.append('99');(PACK/'Earth nav data/apt.dat').write_text('\n'.join(out)+'\n')
    for name in ['sam.xml','opensam.xml']:
        tree=ET.parse(OLD/name);root=tree.getroot();root.set('name','NRT KIAH R24 Headquarters')
        refs=root.find('datarefs');gui=root.find('gui');instances=root.find('objects')
        for item in list(refs):
            if 'private_hangar' in item.get('name','') or 'truck_garage' in item.get('name',''):refs.remove(item)
        for item in list(gui):
            if item.get('instance') in ['private_hangar','truck_service']:gui.remove(item)
        for item in list(instances):
            if item.get('id')=='truck_service':instances.remove(item)
            elif item.get('id')=='private_hangar':item.set('id','indoor_parking')
        for side,ref in [('Left',REF_LEFT),('Right',REF_RIGHT)]:
            data=ET.SubElement(refs,'dataref',name=ref,autoplay='false',randomize_phase='false',augment_wind_speed='false')
            ET.SubElement(data,'animation',t='0',v='1');ET.SubElement(data,'animation',t='60',v='0')
            ET.SubElement(gui,'checkbox',label='Close Indoor Parking '+side,title=side+' sliding doors',instance='indoor_parking',dataref=ref)
        ET.indent(tree);tree.write(PACK/name,encoding='utf-8',xml_declaration=True)

def dsf():
    data=BASE_DSF;raw=(PREV/'qa/R23_Roundtrip.txt').read_text();objects=list(data['objects']);polygons=list(data['polygons']);defs=[];cmd=[]
    def idx(r,obj=False):
        ar=objects if obj else polygons
        if r not in ar:ar.append(r);defs.append(('OBJECT_DEF ' if obj else 'POLYGON_DEF ')+r)
        return ar.index(r)
    def line(r,pts,h=0,fac=False):
        a=[f'BEGIN_POLYGON {idx(r)} {h} {3 if fac else 2}','BEGIN_WINDING']
        for x,y in pts:
            lo,la=g.ag.ll(x,y);a.append(f'POLYGON_POINT {lo:.9f} {la:.9f}'+(' 0' if fac else ''))
        a+=['END_WINDING','END_POLYGON'];return a
    def obj(r,xy,h):
        lo,la=g.ag.ll(*xy);cmd.append(f'OBJECT {idx(r,True)} {lo:.9f} {la:.9f} {h}')
    replaced={'r21_private_hangar','r23_jet_center','r23_identity','r23_ground_ids','r23_ramp_details'}
    for q in data['entities']:
        r=q['resource'];erase=q['kind']=='object' and Path(r).stem in replaced
        if q['kind']=='polygon' and 'jet_blast_deflectors' in r and box(2800,270,3160,770).intersects(q['geom']):erase=True
        # Any still-native old parking guidance in the removed pad/hangar is
        # retired along with its custom painted meshes.
        if q['kind']=='polygon' and '/lines/' in r and box(2646,395,2707,449).covers(q['geom']):erase=True
        if erase:raw=raw.replace('\n'.join(q['lines']),'');retired.append(dict(resource=r,bounds=list(q['geom'].bounds)))
    for path in BLAST_PATHS:cmd+=line('lib/airport/Ramp_Equipment/jet_blast_deflectors/angled_mesh_1.fac',path,5,True)
    for p in g.placements:obj(p['resource'],p['origin'],p['heading'])
    raw=raw.replace('FILTER 0','\n'.join(defs)+'\nFILTER 0',1)+'\nFILTER 0\n'+'\n'.join(cmd)+'\n'
    src=QA/'R24_South.txt';src.write_text(raw)
    dst=PACK/'Earth nav data/+20-100/+29-096.dsf'
    (QA/'Compile.txt').write_text(g.run([g.TOOL,'--text2dsf',src,dst]));(QA/'Decompile.txt').write_text(g.run([g.TOOL,'--dsf2text',dst,QA/'R24_Roundtrip.txt']))

def main():
    prepare();materials();model();parking_hangar();truck_doors_static();cleanup();pedestrian_and_ga();apt();dsf()
    evidence=dict(BASE)
    evidence.update(name=NAME,layout='R24',revision='R21',placements=list(PLACEMENTS.values()),new_placements=g.placements,retired_dsf_entities=retired,clipped_objects=paint_cleanup,runtime_tested=False,
        r24=dict(canopy_nosewheel=NG,passenger_door=DOOR,marshaller=[2648,286],approved_proposal_sha256=sha(APPROVED),arrival=PROPOSAL['arrival'],departure=PROPOSAL['departure'],ga_nosewheel=GA_NG,ga_heading=GA_HEAD,ga_route=GA_ROUTE,ga_planning_vehicle=GA_PLANNING,ga_envelope=GA_BOX.bounds,ga_wingspan_m=20,ga_length_m=22,ga_departure='Pushback or tow out',walk=WALK,ga_walk=GA_WALK,ga_walk_approach='North',blast_paths=BLAST_PATHS,hangar_roof_m=20.6,hangar_clear_opening_m=16,hangar_control_refs=[REF_LEFT,REF_RIGHT],controls=6,truck_doors='Fixed open',beacon=False,headquarters_name='NRT VIRTUAL HEADQUARTERS'))
    (PACK/'Build_Evidence.json').write_text(json.dumps(evidence,indent=2))
    (OUT/'Build_Checks.json').write_text(json.dumps(g.checks,indent=2))
    print(json.dumps(dict(package=str(PACK),new_objects=len(g.placements),retired=len(retired),built=True)))
