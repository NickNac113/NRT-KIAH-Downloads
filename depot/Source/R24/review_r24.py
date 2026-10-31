from pathlib import Path
import sys,importlib.util,json,html,math
from PIL import Image,ImageDraw,ImageFont
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output'
s=importlib.util.spec_from_file_location('r24',ROOT/'source/build_r24.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
v=json.loads((OUT/'Validation.json').read_text())
im=Image.new('RGB',(1800,1420),'#edf0e8');d=ImageDraw.Draw(im)
def font(sz,bold=False):return ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',sz)
x0,y0,x1,y1=2395,270,2910,607;scale=3.15
def pt(q):return (90+(q[0]-x0)*scale,180+(y1-q[1])*scale)
def poly(q,color,edge='#74867e'):
    points=[pt(p) for p in q.exterior.coords];d.polygon(points,fill=color);d.line(points,fill=edge,width=2)
def line(p,color,w):d.line([pt(q) for q in p],fill=color,width=w,joint='curve')
def label(p,t,size=22,bold=False):d.multiline_text(pt(p),t,font=font(size,bold),anchor='mm',fill='#163b43',align='center',spacing=3)
d.text((55,35),'R24  /  Headquarters, canopy and Indoor Parking',font=font(36,True),fill='#163b43')
d.text((55,90),'Built geometry and native guidance  |  North is up  |  Metres',font=font(23),fill='#506961')
poly(b.box(2411,276.6,2890,595),'#d7dbd3')
poly(b.box(2418,488,2512,592),'#abb8b7');label((2465,541),'MH1\nA380 maintenance',21,True)
poly(b.box(2446,434,2512,488),'#abb8b7');label((2479,461),'MH2',22,True)
poly(b.box(2434,284,2512,433.3),'#bccbc8');label((2473,359),'INDOOR\nPARKING\n\n20.6 m roof',22,True)
poly(b.FOOT,'#a9c0c2');label((2811,376),'NRT VIRTUAL\nHEADQUARTERS',24,True)
poly(b.CANOPY,'#c2d4d1');label((2647,333),'CANOPY',20,True)
line([(b.g.SPINE,291),(b.g.SPINE,475)],'#c18a17',6)
for key in ['arrival','departure']:line(b.PROPOSAL[key],'#cf9b25',6)
for col in b.COLS:poly(col,'#324f56')
poly(b.GA_BOX,'#c9d9c4')
poly(b.box(2676,421,2698,441),'#b1c5b0');label((2683,436),'GA',18)
label((2687,414),'NRT11',17,True)
line(b.GA_ROUTE,'#c18a17',4)
walk=b.LineString(b.WALK).buffer(.8,join_style=2,cap_style=2).union(b.LineString(b.GA_WALK).buffer(.8,join_style=2,cap_style=2));poly(walk,'#f9faf2','#238079')
poly(b.box(2652,457,2698,503),'#c8d7cb')
c=pt((2675,480));r=20*scale;d.ellipse((c[0]-r,c[1]-r,c[0]+r,c[1]+r),outline='#fafff8',width=5);label((2675,480),'H',38,True)
label((2675,512),'NRT10  /  ground lighting',20,True)
line([(2675,455),(2675,454)],'#a86245',10)
label((2767,466),'Marked walk\nNorth approach to GA\nHold before helipad',18)
line([(2739,462),(2721,446)],'#66877c',2)
label((2778,435),'GA limit: 20 m wingspan\n22 m planning length\nNose east / pushback out',18)
line([(2739,436),(2699,433)],'#66877c',2)
label((2600,470),'MAIN TAXI LINE',18)
def arrow(center,heading):
    f=b.g.direction(heading);r=b.np.array([f[1],-f[0]]);c=b.np.array(center)
    poly(b.Polygon([c+f*2,c-f*2+r*1.3,c-f*2-r*1.3]),'#7d5a14','#7d5a14')
for p,h in [((2585,423),110),((2648,365),180),((2610,316),270),((2569.8,370),0)]:arrow(p,h)
arrow((2659,430),90);arrow((2692,431),90)
label((2573,280),'Return to spine',18)
line([(2645,314),(2651,314)],'#d49d26',7)
label((2718,303),'New stop + doorway\n11 m north',18)
line([(2691,307),(2674,314.86)],'#66877c',2)
line([(2512,359),(2558,359)],'#c18a17',4)
label((2537,349),'Outward\nstart',17)
label((2445,279),'No old red parking square',17)
line([(2880,550),(2880,580)],'#163b43',4)
poly(b.Polygon([(2878,576),(2880,582),(2882,576)]),'#163b43','#163b43');label((2880,590),'N',21,True)
d.rectangle((0,1300,1800,1420),fill='#f8faf5')
d.text((55,1325),'Yellow: aircraft guidance   /   Green outline: pedestrian walk   /   NRT11: small GA parking',font=font(22),fill='#163b43')
d.text((55,1365),'G650 / Lineage pull-through awaits simulator testing. BBJ2 remains tow-in / tow-out. No beacon.',font=font(22),fill='#506961')
im.save(OUT/'R24_Plan.png')
changes=[
('Canopy pull-through','Native yellow taxi guidance follows the approved entry and forward exit. The stop and passenger doorway move 11 m north; columns and canopy footprint stay in place. G650 and Lineage are the turning targets. BBJ2 remains tow-only.'),
('Indoor Parking','Former Private Hangar renamed on the building, ground marking and start menu. Roof matches MH2: 20.6 m, with 16 m clear doors. Unified corner walls replace the overlapping solids. Left and right sliding-door halves have separate OpenSAM controls, both open by default.'),
('Headquarters and fencing','Both main signs now read NRT VIRTUAL HEADQUARTERS. The old arrival-court fence fabric, posts and rails are removed while the guardhouse and entry barrier remain. The legacy red parking square behind the hangar is removed.'),
('Cargo perimeter','The south blast fence is reversed toward the apron. The south, east and northeast cargo perimeter sections have continuous 5 m native Laminar blast fencing; truck access openings remain usable.'),
('NRT11 and helipad access','NRT11 now parks nose east, following your latest change. The upper taxi branch bends gently into a straight final approach. Departure uses pushback or towing. The GA planning limit is 20 m wingspan and 22 m length. The marked walk follows the stepped headquarters wall, then branches to the GA bay from the north and continues to the NRT10 hold point. Neither aircraft entry crosses the walk. One helipad and its ground lights remain; no beacon.'),
('OpenSAM and jetways','Six controls remain: three MH1 sections, MH2, Indoor Parking Left, Indoor Parking Right. Truck doors are fixed in their open pose. All 119 airport/FBO native jetway records and the existing service routes are preserved.')]
cards=''.join('<article><h2>'+html.escape(t)+'</h2><p>'+html.escape(x)+'</p></article>' for t,x in changes)
imgs=[('R24_Plan.png','Layout and paths'),('Canopy_Pullthrough.png','Exported canopy and guidance'),('Headquarters_Arrival.png','Arrival court after fence cleanup'),('Indoor_Parking_Open.png','Hangar height and open pose'),('Indoor_Parking_Split.png','Independent door example')]
gallery=''.join(f'<section><h2>{title}</h2><a href="{file}"><img src="{file}" alt="{title}"></a></section>' for file,title in imgs)
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NRT R24 Review</title><style>body{margin:0;background:#edf0e9;color:#163b43;font:18px/1.55 Segoe UI,Arial,sans-serif}main{max-width:1220px;margin:40px auto;padding:0 24px}h1{font-size:44px;line-height:1.15}h2{font-size:24px}.tag{letter-spacing:.12em;color:#61786e;font-size:14px}a{color:#216c78}article,section,.notice{background:#fafff7;padding:22px 28px;border-radius:10px;margin:22px 0}img{width:100%;height:auto}#cards{display:grid;grid-template-columns:1fr 1fr;gap:20px}#cards article{margin:0}li{margin:.5em 0}@media(max-width:800px){#cards{display:block}h1{font-size:32px}}small{color:#586e65}</style><main><div class="tag">NRT / KIAH / R24 TEST BUILD</div><h1>Pull-through and campus refinements</h1><p>Approved canopy routing, Indoor Parking, corrected fencing and a marked route to the helipad.</p><div class="notice"><strong>Offline checks passed.</strong> Actual X-Plane appearance, add-on steering, OpenSAM docking and door operation still need the next simulator test. This build is packaged locally; it has not replaced the public SkunkCrafts feed.</div><p><a href="Install_and_Test.txt">Install and test instructions</a> · <a href="Validation.json">Geometry and preservation evidence</a></p><div id="cards">'''+cards+'</div>'+gallery+'''<section><h2>Test on the new PC</h2><ol><li>Install this isolated revision with X-Plane closed, then launch fresh and load KIAH.</li><li>Taxi the G650 or Lineage into NRT CANOPY and follow the forward exit back to the spine. Check wheel tracking, column clearance and the new stop/door alignment.</li><li>Test Indoor Parking Left and Right separately. Confirm the unselected half stays still and both default open after a new load.</li><li>Inspect the wall corners, arrival court, rear red-paint cleanup, all blast fence runs, NRT11 and the pedestrian hold point.</li><li>Confirm terminal and FBO jetways still load. Aircraft-door and marshaller behavior depends on the add-on.</li></ol><p>BBJ2 is not part of the forward-turn requirement. The pedestrian route is ground paint; use it only with aircraft stopped and helicopter rotors stopped.</p></section><small>Exports and review images are not X-Plane screenshots. No plugins or installed scenery were changed.</small></main></html>'''
(OUT/'Review.html').write_text(page,encoding='utf-8')
(OUT/'Change_List.json').write_text(json.dumps(changes,indent=2))
print('Wrote plan and review')
