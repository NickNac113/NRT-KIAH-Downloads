from airport_geometry import *
from shapely.ops import nearest_points
from shapely.affinity import rotate,translate

APT=ROOT/'KIAH-99761/KIAH.dat'
DSF=ROOT/'compiler-check/+29-096.txt'
OUT=ROOT.parent/'outputs'
PACK=OUT/'KIAH_2026-10-24_Review_R02'
DATE='2026-10-24'
def geobox(w,s,e,n):
    a=xy(w,s);b=xy(e,n);return box(*a,*b)
def heading_vec(h):
    r=math.radians(h);return np.array([math.sin(r),math.cos(r)])
def bearing(v):return math.degrees(math.atan2(v[0],v[1]))%360
def aircraft_outline(pos,h,size='C'):
    # Ground-clearance guide: reference point at the nose wheel, not a survey.
    length,span={'A':(14,15),'B':(30,24),'C':(40,36),'D':(55,52),'E':(74,65),'F':(74,80)}[size]
    f=heading_vec(h);right=np.array([f[1],-f[0]]);pos=np.asarray(pos)
    profile=[(0,4),(2,1),(2,-length*.35),(span/2,-length*.62),(span/2,-length*.67),(2,-length*.50),(1.6,-length*.81),(span*.17,-length*.90),(span*.17,-length*.94),(0,-length+4),(-span*.17,-length*.94),(-span*.17,-length*.90),(-1.6,-length*.81),(-2,-length*.50),(-span/2,-length*.67),(-span/2,-length*.62),(-2,-length*.35),(-2,1)]
    return Polygon([pos+right*x+f*y for x,y in profile])
def build_plan():
    apt=parse_apt(APT);dsf=parse_dsf(DSF);buildings,gates,floors=current_sources();gd={g['name']:g for g in gates}
    bn=polys_only(buildings['iah-tb-2'].intersection(geobox(-95.348,29.98730,-95.3429,29.9901))).simplify(.25,preserve_topology=True)
    dw=polys_only(buildings['iah-td-2'].intersection(geobox(-95.3395,29.98753,-95.3380,29.9902))).simplify(.25,preserve_topology=True)
    icp=polys_only(unary_union([buildings['iah-te-1'],buildings['iah-te-2']]).intersection(geobox(-95.33490,29.98610,-95.33160,29.98746))).simplify(.35,preserve_topology=True)
    # B ticketing core is physically present but its public lobby is closed in this snapshot.
    bc=polys_only(buildings['iah-tb-2'].intersection(geobox(-95.3462,29.9860,-95.3440,29.9873))).simplify(.25,preserve_topology=True)
    models={'B_North':{'geom':bn,'height':15.5,'style':'silver','evidence':'Houston Airports 2026-10-23 outline; heights and roof details interpreted'},'D_West':{'geom':dw,'height':15.0,'style':'silver','evidence':'Houston Airports current outline; heights and roof details interpreted'},'International_Processor':{'geom':icp,'height':17.0,'style':'silver','evidence':'Houston Airports current outline; heights and roof details interpreted'},'B_Lobby_Closed':{'geom':bc,'height':15.0,'style':'silver','evidence':'Current outline; lobby remains closed per Houston Airports alert'}}
    # Disjoint focused work areas; adjoining unchanged C, Skyway, parking and B South are retained.
    zones={'B_North':geobox(-95.3482,29.98738,-95.34350,29.99055),'D_West':geobox(-95.33960,29.98770,-95.33792,29.99068),'International_Processor':icp.buffer(2),'B_Lobby_Closed':bc.buffer(1)}
    bn_h={1:282,2:270,3:260,4:230,5:195,6:160,7:130,8:105,9:90,10:180,11:180,12:270,14:270,15:260,16:230,17:195,18:160,19:130,20:105,21:115,22:65,23:90}
    new=[]
    for num,h in bn_h.items():
        n=f'B{num}';g=gd[n];p=np.array(g['point'].coords[0]);f=heading_vec(h)
        # 15-28m modeled nose-wheel clearance from boarding door; tips fan outward.
        distance=28 if num in (3,4,5,6,7,15,16,17,18,19) else 18
        if num in (10,11):distance=24
        pos=p-f*distance
        new.append(dict(name=n,pos=pos.tolist(),heading=h,size='C',kind='gate',airlines='ual',source='modeled from current gate door and terminal footprint',door=p.tolist(),model='B_North'))
    for num,h in {1:270,2:90,3:270,4:110,5:250,6:180}.items():
        pair=[gd[f'D{num}{s}'] for s in ('A','B') if f'D{num}{s}' in gd]
        p=np.mean([g['point'].coords[0] for g in pair],axis=0) if pair else np.array(gd[f'D{num}']['point'].coords[0])
        dist=32 if num<4 else 38
        pos=p-heading_vec(h)*dist
        new.append(dict(name=f'D{num}',pos=pos.tolist(),heading=h,size='E',kind='gate',airlines='',source='modeled MARS wide-body position from current door group',door=p.tolist(),model='D_West'))
        for j,g in enumerate(pair):
            f=heading_vec(h);right=np.array([f[1],-f[0]])
            pp=pos+right*((j-.5)*40)+f*7
            new.append(dict(name=g['name'],pos=pp.tolist(),heading=h,size='C',kind='misc',airlines='',source='manual-select MARS alternative; mutually exclusive with parent wide-body gate',door=list(g['point'].coords[0]),model='D_West',alternative=True,parent=f'D{num}'))
    south={11:48,10:47,9:46,3:40,8:45,5:41,7:44,6:43,4:42,20:57,12:50,19:56,14:51,18:55,15:52,16:53,17:54,21:60,31:68,30:67,22:61,29:66,23:62,28:65,24:63,26:64}
    drename={'D1':'D7','D2':'D8','D2W':'D8 wide','D3':'D9','D4':'D10','D5':'D11','D6':'D12','D7':'D14','D8':'D15','D9':'D16','D9A':'D16 A380','D10':'D17','D11':'D18A','D12':'D18B','D12A':'D18 wide'}
    ramps=[];removed=[]
    for a in apt:
        if a['code']!=1300:continue
        old=a['name'];name=old.removeprefix('Gate ');r=dict(a);r['old_name']=old
        if old in [f'Terminal A Stand {i}' for i in range(1,5)]:
            removed.append(old);continue
        is_old_dwest=re.match(r'C(16|17|18|19|20|21|22|23|24|24W)$',name)
        if is_old_dwest:removed.append(old);continue
        if re.match(r'B\d',name):
            num=int(re.search(r'\d+',name)[0])
            if a['lat']>29.987 or num not in south:removed.append(old);continue
            r['name']='Gate B'+str(south[num]);r['source']='2023 stand retained; renumbered to 2026 B South published gate'
            # South positions retained as B size where established: do not silently enable larger aircraft.
        elif name in drename:
            r['name']='Gate '+drename[name];r['source']='existing D apron position; 2026 gate renumbering'
            if name.endswith(('W','A')):r['kind']='misc'
        else:r['source']='retained Gateway 99761 position'
        if name in ('C12','C14','C15'):
            h=125 if name=='C12' else 180;pos=np.array(gd[name]['point'].coords[0])-heading_vec(h)*(20 if name=='C12' else 22)
            lon,lat=ll(*pos);r.update(lon=lon,lat=lat,heading=h,geom=Point(pos),source='position adjusted to current C connector gate door; modeled stop point')
        if name=='C14W':
            pos=np.array(gd['C14']['point'].coords[0])-heading_vec(180)*22
            lon,lat=ll(*pos);r.update(lon=lon,lat=lat,heading=180,geom=Point(pos),kind='misc',name='Gate C14 wide',source='manual wide-body alternative to C14')
        if name in ('E2W','E20W'):
            r['kind']='misc';r['name']='Gate '+name[:-1]+' wide'
            r['source']='Retained wide-body alternative; manual only to prevent automatic overlap with neighboring stands'
        if r['name'].startswith(('Gate B','Gate C','Gate E')) and r['kind']=='gate':
            r['rampmeta']=r.get('rampmeta',['1301','C','airline'])[:3]+['ual']
        ramps.append(r)
    for r in new:
        lon,lat=ll(*r['pos']);r.update(lat=lat,lon=lon,geom=Point(r['pos']),equipment='heavy|jets' if r['size'] in 'DEF' else 'jets',rampmeta=['1301',r['size'],'airline' if r['kind']=='gate' else 'none']+r['airlines'].split(),old_name=None)
        ramps.append(dict(r,name='Gate '+r['name']))
    # A20 is an aircraft stand, independently mapped as a painted parking lead-in.
    # Use the terminal end of OSM way 1362706405; imagery confirms the southern jetway.
    a20pos=xy(-95.3493553,29.9847632)
    a20h=bearing(np.array(a20pos)-np.array(xy(-95.3492044,29.9843962)))
    a20=dict(name='A20',pos=list(a20pos),heading=a20h,size='C',kind='gate',airlines='',
        door=list(xy(-95.349556,29.985003)),source='OSM mapped aircraft lead-in, checked against Vantor aerial; modeled nose-wheel stop',
        building=buildings['iah-ta-2'],old_name=None,model='Terminal_A')
    lon,lat=ll(*a20pos)
    ramps.append(dict(a20,name='Gate A20',lat=lat,lon=lon,geom=Point(a20pos),equipment='jets',rampmeta=['1301','C','airline']))
    details=[a20]
    for n in ('C12','C14','C15'):
        r=next(r for r in ramps if r['name']=='Gate '+n)
        details.append(dict(name=n,pos=list(r['geom'].coords[0]),heading=r['heading'],size='C',kind='gate',
            door=list(gd[n]['point'].coords[0]),building=buildings['iah-tc-2'],model='Terminal_C',source=r['source']))
    inactive={
        'C29':{'decision':'No aircraft spawn: removed stand footprint',
            'basis':'2015 permanent gate-removal chart notice archived by NTSB; 2025 aerial shows service space and no stand/jetway. Passenger map still lists C29.',
            'confidence':'Evidence supports omission; reopening after aerial capture not independently confirmed.'},
        'E6':{'decision':'No aircraft spawn: former stand within E5/E7 apron',
            'basis':'2025 aerial and mapped aircraft lead-ins show no independent E6 stand between E5 and E7. Historical removal report is supporting evidence only. Passenger map still lists E6.',
            'confidence':'Conservative scenery interpretation; no current airport-issued stand-allocation drawing obtained.'}}
    return dict(apt=apt,dsf=dsf,buildings=buildings,gates=gates,models=models,zones=zones,new=new,ramps=ramps,removed=removed,details=details,inactive=inactive)

def audit_plot(plan,path):
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(18,10));ax.set_facecolor('#23323c');fig.patch.set_facecolor('#14222d')
    for a in plan['apt']:
        if a['code']==110:draw_geom(ax,a['geom'],facecolor='#56636a',edgecolor='#66757b',linewidth=.25)
    for k,v in plan['models'].items():draw_geom(ax,v['geom'],facecolor='#dde4e4',edgecolor='#54f6c8',linewidth=1)
    for r in plan['new']:
        if r.get('alternative'):continue
        g=aircraft_outline(r['pos'],r['heading'],r['size']);draw_geom(ax,g,facecolor='#8ab2c5',edgecolor='white',linewidth=.5)
        p=np.asarray(r['pos']);d=np.asarray(r['door']);ax.plot([p[0],d[0]],[p[1],d[1]],color='#ffb955',linewidth=.7)
        ax.text(*p,r['name'],fontsize=7,color='#ffeea0',ha='center',va='center')
    nodes={a['id']:xy(a['lon'],a['lat']) for a in plan['apt'] if a['code']==1201}
    for a in plan['apt']:
        if a['code']==1202:
            p,q=nodes[a['start']],nodes[a['end']];ax.plot([p[0],q[0]],[p[1],q[1]],color='#ff8855',lw=.4)
    ax.set_xlim(-700,500);ax.set_ylim(280,790);ax.set_aspect('equal');ax.tick_params(colors='white');ax.set_title('B North / D West modeled aircraft envelopes and inherited routing',color='white')
    fig.tight_layout();fig.savefig(path,dpi=140);plt.close(fig)
if __name__=='__main__':
    p=build_plan();audit_plot(p,ROOT/'stand-audit.png')
    print('new ramps',len(p['new']),'total ramps',len(p['ramps']),'removed',len(p['removed']))
    for m,v in p['models'].items():print(m,round(v['geom'].area),v['geom'].bounds)
    solids=unary_union([v['geom'] for v in p['models'].values()])
    prim=[r for r in p['new'] if not r.get('alternative')]
    for i,r in enumerate(prim):
        a=aircraft_outline(r['pos'],r['heading'],r['size'])
        if a.intersects(solids):print('BUILDING CONFLICT',r['name'],round(a.intersection(solids).area,2))
        for q in prim[i+1:]:
            b=aircraft_outline(q['pos'],q['heading'],q['size'])
            if a.distance(b)<3:print('ENVELOPE',r['name'],q['name'],round(a.distance(b),1),'area',round(a.intersection(b).area,1))
