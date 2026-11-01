"""Dimensioned exported-data plans. No claim of simulator light rendering."""
from pathlib import Path
import importlib.util,sys,json,math
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('r26',ROOT/'source/build_r26.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
g=b.g;OUT=b.OUT;E=json.loads((b.PACK/'Build_Evidence.json').read_text())['r26'];V=json.loads((OUT/'Validation.json').read_text())
ap=g.ag.parse_apt(b.PACK/'Earth nav data/apt.dat');dsf=g.ag.parse_dsf(b.QA/'R26_Roundtrip.txt')
font=lambda n,bold=False:ImageFont.truetype('C:/Windows/Fonts/'+('arialbd.ttf' if bold else 'arial.ttf'),n)

def plan(bounds,size,title,subtitle):
    im=Image.new('RGB',size,'#edf0ed');d=ImageDraw.Draw(im)
    d.rectangle((0,0,size[0],106),fill='#183940');d.text((34,21),title,font=font(32,True),fill='white');d.text((34,65),subtitle,font=font(20),fill='#d8e4e4')
    left,top=60,146;scale=min((size[0]-120)/(bounds[2]-bounds[0]),(size[1]-330)/(bounds[3]-bounds[1]))
    def p(xy):return (left+(xy[0]-bounds[0])*scale,top+(bounds[3]-xy[1])*scale)
    def poly(geo,fill,outline='#8d9994',width=2):
        geo=geo.intersection(b.box(*bounds))
        for q in g.parts(geo):
            if q.geom_type!='Polygon':continue
            pts=[p(x) for x in q.exterior.coords];d.polygon(pts,fill=fill);d.line(pts,fill=outline,width=width)
            for ring in q.interiors:d.polygon([p(x) for x in ring.coords],fill='#edf0ed')
    def line(xy,col,width=3):
        for ln in g.lines(b.Line(xy).intersection(b.box(*bounds))):d.line([p(x) for x in ln.coords],fill=col,width=width,joint='curve')
    def label(xy,text,col='#163940',sz=19):d.multiline_text(p(xy),text,font=font(sz,True),fill=col,anchor='mm',align='center',spacing=4)
    clip=b.box(*bounds)
    for q in ap:
        if q['code']==110 and q['geom'].intersects(clip):poly(q['geom'].intersection(clip),'#d4d8d2','#bac1b8',1)
    for q in dsf['entities']:
        if q['kind']=='polygon' and '/pavement/' in q['resource'] and q['geom'].intersects(clip):poly(q['geom'].intersection(clip),'#dce0da','#c5ccc3',1)
    poly(b.b.FOOT.intersection(clip),'#9db5b8','#3d666c',2)
    poly(b.b.CANOPY.intersection(clip),'#bfcfca','#6a8f8b',2)
    north=(size[0]-65,150);d.line([north,(north[0],north[1]+55)],fill='#183940',width=4);d.polygon([(north[0],north[1]-4),(north[0]-8,north[1]+15),(north[0]+8,north[1]+15)],fill='#183940');d.text((north[0],north[1]-19),'N',font=font(20,True),fill='#183940',anchor='mm')
    return im,d,p,poly,line,label,scale

im,d,p,poly,line,label,scale=plan((2395,270,3140,790),(2200,2050),'R26  |  Work lighting + paved service access','22 new wall-mounted lights; 9 existing canopy lamps upgraded. North is up.')
for stem,name in [('mx_stepped_hangar','MH1'),('mh2_accordion_hangar','MH2'),('r24_indoor_parking','INDOOR\nPARKING'),('cargo','CARGO')]:
    rel='objects/nrt_test/'+stem+'.obj';q=b.PLACEMENTS[rel]
    v=b.np.array([[float(a) for a in r.split()[1:4]] for r in (b.PACK/rel).read_text().splitlines() if r.startswith('VT ')])
    rect=(v[:,0].min()+q['geom'].x,q['geom'].y-v[:,2].max(),v[:,0].max()+q['geom'].x,q['geom'].y-v[:,2].min())
    poly(b.box(*rect),'#a7b9b9','#5a787c');label(((rect[0]+rect[2])/2,(rect[1]+rect[3])/2),name,sz=18)
label((2800,370),'NRT VIRTUAL\nHEADQUARTERS',sz=22);label((2646,316),'CANOPY',sz=17)
poly(b.HELI,'#c6d3be','#96aa8d');poly(b.Point(b.b.HELI).buffer(20),'#ccd8c4','#f7fbf7',3);label(b.b.HELI,'H',sz=35)
label((2675,514),'NRT10\nGround lighting only',sz=17)
line(b.WALK,'#207d83',4);line(b.GA_WALK,'#207d83',4)
for q in ap:
    if q['code']==1300 and q['name'] in ['NRT'+str(n) for n in range(1,12) if n!=10]:
        xy=[q['geom'].x,q['geom'].y];x,y=p(xy);d.ellipse((x-3,y-3,x+3,y+3),fill='#806b1d');label((xy[0],xy[1]-8),q['name'].replace('NRT Indoor Parking','Indoor'),sz=14)
for mark in E['service_paths']:line(mark['points'],'#2078ab',7)
poly(b.SERVICE_LINK,'#e3b55a','#a5681a',3)
for l in E['lights']:
    xy=l['position'][:2];t=l['target'][:2];x,y=p(xy)
    if xy!=t:line([xy,t],'#b29133',2)
    d.ellipse((x-6,y-6,x+6,y+6),fill='#efbb37',outline='#72581a',width=2)
label((2785,621),'New paved connector\nacross existing grass gap',sz=17)
line([(2785,613),(2813.27,598)],'#9b681f',2)
label((2917,516),'Native airport service roads\n6 m marked corridor',col='#1a6895',sz=17)
label((2570,362),'Wall-mounted\nhangar lights',sz=16)
d.rectangle((28,1838,2172,2020),fill='white',outline='#c3ceca')
for i,t in enumerate(['Yellow dots: work-light locations; short rays show ground aim, not simulated light coverage.',
                      'Blue: new connected service network. Existing airport roads, service fleet and crew-car loop retained.',
                      'All new fixtures remain more than 50 m from the helipad reserve; no poles or beacon added.',
                      'Offline plan only. Night brightness, frame time and service-vehicle movements require X-Plane testing.']):
    d.text((50,1855+i*37),t,font=font(22),fill='#24464d')
im.save(OUT/'R26_Lighting_Service_Plan.png')

im,d,p,poly,line,label,scale=plan((2650,410,2888,540),(2200,1590),'R26  |  NRT9 pedestrian separation','NRT9 moves 4 m east, keeping its heading. Building-side walking path and fixed jetway bases stay in place.')
n=b.NRT9;old=b.box(n[0]-4-79.75/2,n[1]-3,n[0]-4+79.75/2,n[1]+70);new=b.box(n[0]-79.75/2,n[1]-3,n[0]+79.75/2,n[1]+70)
n8=b.box(2842.527-44.84/2,435,2842.527+44.84/2,490)
poly(old,'#d8cfc2','#9c8a71',2);poly(new,'#b9d4c7','#35755a',4);poly(n8,'#bdcbd4','#4f7287',3)
poly(b.HELI,'#c6d3be','#6e8b67',2);poly(b.Point(b.b.HELI).buffer(20),'#c6d3be','#f5f9f3',3);label(b.b.HELI,'H',sz=44)
poly(b.Line(b.WALK).buffer(.8,cap_style=2,join_style=2),'#238d92','#176b70',2);line(b.GA_WALK,'#238d92',4)
for mark in E['service_paths']:
    for part in g.lines(b.Line(mark['points']).intersection(b.box(2650,410,2888,540))):line(part.coords,'#237caa',7)
line([(n[0],n[1]),(n[0],528)],'#b58a18',4);line([(2842.527,438),(2842.527,512)],'#b58a18',4)
label((n[0],475),'NRT9\nFull A380 planning envelope\n79.75 m span',col='#2a644b',sz=24)
label((2842.527,466),'NRT8\nA300 envelope',col='#355b73',sz=23)
label((2680,437),'Marked walk\nkept beside building',col='#176b70',sz=19)
line([(2700,440),(2720.2,440)],'#176b70',2)
label((2723,518),'4.47 m\nwalk clearance',col='#176b70',sz=18)
line([(2721.8,509),(2721.8,514),(n[0]-79.75/2,514),(n[0]-79.75/2,509)],'#176b70',3)
label((2813.3,525),'Service access\non pavement',col='#20638e',sz=19)
label((2760,533),'Tan outline = previous NRT9 position',col='#806f58',sz=17)
for j in b.EVIDENCE['jetways']:
    x,y=p(j['base']);d.rectangle((x-7,y-7,x+7,y+7),fill='#48606b');label((j['base'][0],j['base'][1]-4),j['id'],sz=17)
d.rectangle((28,1305,2172,1560),fill='white',outline='#c3ceca')
for i,t in enumerate(['The start, disconnected guidance line, stand outline, stop marks and ground label move together.',
                      '4.47 m to the full parked A380 rectangle; 14.09 m between the NRT8 and NRT9 planning envelopes.',
                      'Fixed links and all 119 native jetway definitions are unchanged. Add-on docking still needs a test.',
                      'NRT11 remains nose east with the accepted 66 m wingspan / 50 m length limit.',
                      'Rectangles are conservative planning envelopes, not simulator aircraft screenshots.']):
    d.text((50,1324+i*43),t,font=font(23),fill='#24464d')
im.save(OUT/'R26_NRT9_Clearance.png')

review='''R26 LIGHTING, PEDESTRIAN SEPARATION AND SERVICE ACCESS

22 new lights: 15 terminal / NRT11 / pedestrian work lights and 7 hangar
apron lights. Nine existing canopy lamps are upgraded at their original
15.7 m mounting height. All new emitters are directional and night-only.
No mast or beacon added near the single ground-lit helipad.

NRT9 moves 4 m east with its start, disconnected yellow guidance line,
stop bars, ground wording and stand boundary. The walking corridor stays
at the building. Full parked A380 rectangle is 4.47 m from the corridor;
NRT8 / NRT9 planning envelopes retain 14.09 m separation. Fixed jetway
connections and 119 native animated-jetway records remain unchanged.

The NB service routes were inherited from the base airport. R25 had no
connected NRT airside service branch. R26 adds 59 connected nodes / edges,
with a 6 m marked road corridor, and a small native paved connector over
the approximately 7 m grass gap to the old road. Exported road geometry
stays on pavement and clear of the checked occupied stand envelopes.
This is a route correction for testing, not proof every reported grass
crossing is resolved. X-Plane controls the final approach off the network.

TEST NEXT
1. Dusk / night: NRT8, NRT9, NRT11, canopy and hangar apron illumination;
   compare frame time from the same camera. Helipad remains ground-lit.
2. NRT9: full-size parked aircraft, walking clearance, each native jetway.
3. Request fuel / baggage / service vehicles at NRT1-9. Follow the route
   from NB and the final approach to the aircraft. The landside crew-car
   loop is retained separately. Aircraft movements retain right of way.

No AEP required. Six default-open independent OpenSAM door controls,
security / blast fences, NRT11, main taxi routes and other starts retained.
Offline checks and exported-model previews do not establish simulator
appearance, animation, traffic or performance acceptance.

REFERENCE
Laminar service-vehicle network authoring:
https://developer.x-plane.com/manuals/wed/#specifyingservicevehiclenetworks
Laminar parameterized lighting:
https://developer.x-plane.com/article/airplane-parameterized-light-guide/
Definitions also checked in the installed stock lights.txt.
'''
(OUT/'Review.txt').write_text(review)
print(json.dumps(dict(plans=2,offline_checks=V['passed'])))
