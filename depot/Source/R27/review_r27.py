"""Measured layout review from the exported R27 airport and DSF."""
from pathlib import Path
import importlib.util,sys,json,math
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('r27',ROOT/'source/build_r27.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.g;OUT=b.OUT;E=json.loads((b.PACK/'Build_Evidence.json').read_text())['r27'];V=json.loads((OUT/'Validation.json').read_text())
ap=g.ag.parse_apt(b.PACK/'Earth nav data/apt.dat');ds=g.ag.parse_dsf(b.QA/'R27_Roundtrip.txt')
nodes={q['id']:g.ag.xy(q['lon'],q['lat']) for q in ap if q['code']==1201}
paved=b.union([q['geom'] for q in ap if q['code'] in [100,110]]+[q['geom'] for q in ds['entities'] if q['kind']=='polygon' and '/pavement/' in q['resource']])
F=lambda z,bold=False:ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),z)
BG='#f6f5ef';INK='#18343e';ROAD='#167e9c';NEW='#cb601a';ROOF='#8aa5ad';DRY='#a7cbaa'
im=Image.new('RGB',(2000,1540),BG);d=ImageDraw.Draw(im)
d.text((45,26),'R27 | Sheltered floors and service access',font=F(35,True),fill=INK)
d.text((45,75),'Measured exported layout. Live traffic, wet-weather appearance, docking and night lighting still need X-Plane testing.',font=F(21),fill=INK)
extent=(2395,270,3120,620);rect=(40,132,1960,1020);scale=min((rect[2]-rect[0])/(extent[2]-extent[0]),(rect[3]-rect[1])/(extent[3]-extent[1]))
def pt(p):return (rect[0]+(p[0]-extent[0])*scale,rect[3]-(p[1]-extent[1])*scale)
def geom(shape,fill=None,outline=None,width=1):
    for p in g.parts(shape):
        d.polygon([pt(v) for v in p.exterior.coords],fill=fill,outline=outline,width=width)
        for h in p.interiors:d.polygon([pt(v) for v in h.coords],fill='#d8dfce')
def ln(points,color,width=2):d.line([pt(p) for p in points],fill=color,width=width,joint='curve')
def label(p,text,size=18,fill=INK,anchor='mm'):d.text(pt(p),text,font=F(size),fill=fill,anchor=anchor,align='center')
geom(b.box(*extent),'#d8dfce');geom(paved.intersection(b.box(*extent)),'#e6e6e0')
geom(b.r25.FOOT,ROOF,INK);geom(b.box(2417.94,487.95,2513.01,591.99),ROOF,INK)
geom(b.box(2445.89,433.82,2512.76,487.82),ROOF,INK);geom(b.box(2434,284,2512,433.3),'#c7d1d0',INK)
geom(b.box(3055.83,548.92,3095.6,620),ROOF,INK)
geom(b.r25.CANOPY,'#c7d1d0',INK)
for shape in b.FLOORS.values():geom(shape,DRY,'#5b8962',2)
for q in ap:
    if q['code']==120 and q.get('geom') is not None:
        for line in g.lines(q['geom'].intersection(b.box(*extent))):ln(line.coords,'#c39b26',2)
for q in ap:
    if q['code']==1206:
        a,c=map(int,q['parts'][1:3]);line=b.Line([nodes[a],nodes[c]]).intersection(b.box(*extent))
        for p in g.lines(line):ln(p.coords,NEW if 'NRT R27' in q['lines'][0] else ROAD,3)
walk=b.Line(b.r25.WALK).buffer(.8,cap_style=2,join_style=2).union(b.Line(b.r25.GA_WALK).buffer(.8,cap_style=2))
geom(walk,'#507b6b')
geom(b.r25.HELI_RESERVE,None,'#6d977d',2);c=pt(b.r25.HELI);rr=20*scale;d.ellipse((c[0]-rr,c[1]-rr,c[0]+rr,c[1]+rr),outline='white',width=5);label(b.r25.HELI,'H',34)
label((2675,511),'NRT10 / ground lights',17)
for p in E['vehicle_parking']:
    x,y=p['xy'];geom(b.box(x-5,y-2.1,x+10,y+2.1),'#c8a779','#815426')
label((2937,486),'7 local service\nvehicle spaces',18)
label((2467,541),'MH1',24);label((2476,461),'MH2',22);label((2473,373),'INDOOR\nPARKING\n\nModeled floor',22)
label((2794,371),'NRT VIRTUAL\nHEADQUARTERS',24);label((2646,341),'CANOPY',19)
label((2646,305),'Modeled floor',15)
label((2693,411),'NRT11\nNose east',19)
nose=b.EVIDENCE['r26']['nrt9_nosewheel'];geom(b.box(nose[0]-79.75/2,nose[1]-3,nose[0]+79.75/2,nose[1]+70),None,'#a4adb0',2)
label((2766,481),'NRT9\nStand unchanged',18);label((2843,474),'NRT8',18)
for j in E['jetways']:
    ln([j['root'],j['base']],'#154457',8)
    x,y=pt(j['base']);d.ellipse((x-5,y-5,x+5,y+5),fill='#154457')
    if j['stand']=='NRT9':label((j['base'][0]+3,j['base'][1]+11),j['id'],16)
ln([(2794,440),(2810,458),(2820,458)],'#154457',2);label((2821,459),'Both arms +4 m east',17,anchor='ls')
p=pt(b.MAST);d.ellipse((p[0]-8,p[1]-8,p[0]+8,p[1]+8),fill='#edb52a',outline=INK,width=2)
ln([b.MAST,(2710,438),(2710,447)],INK);label((2710,451),'New corner mast',17)
ln([(b.MAST[0],b.MAST[1]),(2698,457)],'#a1a99b',1)
label((2584,601),'NB / existing service corridor',18)
label((2997,572),'Cargo access',18)
label((2607,489),'New west\nairside road',17,anchor='rm')
ln([(3092,342),(3092,368)],INK,4);label((3092,377),'N',23)
# Legend and factual limits, kept out of the plan.
for x,col,txt in [(55,NEW,'R27 service routing'),(475,ROAD,'Retained service roads'),(940,DRY,'Added modeled dry floors'),(1510,'#edb52a','New stock mast')]:
    d.rectangle((x,1060,x+34,1082),fill=col);d.text((x+48,1056),txt,font=F(23),fill=INK)
lines=[
 'SERVICE VEHICLES: paved local staging and a western apron road; more access nodes on long NB segments.',
 'ROUTING LIMIT: X-Plane chooses the final approach off its road graph. This build needs a repeat service call at NB.',
 'NRT9: both native arms, rotundas, terminal portals and red movement boxes move 4 m east with the existing stand.',
 'SHELTER: canopy and Indoor Parking receive the same modeled-floor treatment used by the dry maintenance hangars.',
 'MAST: matching NRT8 asset at the HQ corner; 43.3 m outside the helipad square, 76.1 m from its centre.',
 'RETAINED: all starts, main aircraft taxi lines, one helipad, six default-open door controls, secure ramp fencing.',
 'No AEP required. No public SkunkCrafts update in this test build.'
]
for i,t in enumerate(lines):d.text((55,1126+i*48),t,font=F(22),fill=INK)
im.save(OUT/'R27_Repair_Plan.png')
review=f'''NRT KIAH R27 - Shelter, NRT9 alignment, corner mast and service access

BUILT LOCAL TEST - not a public SkunkCrafts release.

The R26 service-road graph was connected and the inspected NB corridor lay
on pavement. The screenshot alone does not establish why native vehicles
leave it. R27 adds a nearby native service fleet, paved access west of the
headquarters, and shorter graph segments on the NB approach. This addresses
dispatch distance and route entry/exit choices; it is not a verified runtime
cure for all X-Plane service-vehicle behavior.

Changes
- Seven native service parking locations on the apron east of headquarters:
  catering, GPU, loader, baggage train, liner fuel, jet fuel and pushback.
  Shared native holding destination, connected to the retained road graph.
- Full new road width is paved. No intersections with occupied stand
  envelopes, buildings, the helipad reserve or the pedestrian corridor.
- 124 additional service nodes and 43 new local edges. Five existing road
  edges are split without changing their geometry; access spacing <=20 m
  on the selected NB stretches. Public car-park loop remains separate.
- NRT9: both native animated jetways, fixed connections, facade portals and
  red movement boxes moved east 4 m. No second stand movement.
- One stock Laminar flood_1_led_24m_omni mast at the requested HQ corner.
  Base clearances: 2.24 m to building, 2.16 m to walk, 6.96 m to the NRT11
  planning rectangle, 12.81 m to NRT9 and 43.31 m to helipad reserve.
  This is the requested one-pad corner layout, not the old two-pad setback.
  These are simulator geometry measurements, not an aerodrome certification.
- Canopy and Indoor Parking: non-draped modeled floors at 0.03 m, matching
  MH1/MH2's floor material. Canopy/indoor guidance remains above the floor.
  Exterior native wet surfaces are unchanged. Rain particles are untested.

Verification
{V['passed']} offline exported-file, geometry, resource, graph and preservation
checks passed. DSF compiled and reopened; max coordinate drift 0.184 m.
All resources resolve using the package, stock X-Plane, MisterX and OpenSAM.
AEP is not required. R26 and the public updater payload remain byte-identical.

Review images
R27_Repair_Plan.png: measured plan; lighting icons are locations, not lux.
R27_Corner_Jetways.png: actual exported mast and fixed terminal connections.
R27_Canopy_Floor.png and R27_Indoor_Floor.png: actual exported floor geometry.
Offline renders do not show native animated arms or simulate X-Plane weather.

Simulator test sequence
1. Fully exit and relaunch X-Plane after installing R27; load KIAH.
2. At NRT9, call catering/fuel/baggage. Observe both dispatch and return,
   especially along NB. Repeat at cargo and canopy with AI traffic enabled.
3. Check NRT9 front and rear jetway docking with your normal aircraft.
4. Set wet weather and compare canopy/Indoor Parking floors against MH1/MH2;
   check the boundaries and guidance at ground level.
5. At night, check corner mast light spill, pedestrian visibility, helipad
   clearance and frame time. Inspect the service staging row in daylight.

If a vehicle still crosses the field, note its origin/destination and
whether it is servicing your aircraft or roaming. The crossing's location
and the active package name in Log.txt will distinguish routing from a
different traffic source or stale package selection.

Primary technical references
https://developer.x-plane.com/manuals/wed/#specifyingservicevehiclenetworks
https://developer.x-plane.com/article/tips-for-getting-your-airport-approved-on-the-gateway/
https://developer.x-plane.com/article/customizing-ground-vehicles/
'''
(OUT/'Review.txt').write_text(review)
print('Plan and readable review saved.')
