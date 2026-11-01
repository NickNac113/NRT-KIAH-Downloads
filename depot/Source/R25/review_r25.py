"""Readable review PDF and measured plan; no browser or simulator required."""
from pathlib import Path
import sys,importlib.util,json,math
from PIL import Image,ImageDraw,ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output';PDF=OUT/'pdf';PDF.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('r25',ROOT/'source/build_r25.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
v=json.loads((OUT/'Validation.json').read_text())
im=Image.new('RGB',(1800,1280),'#eff2ec');d=ImageDraw.Draw(im)
font=lambda sz,bold=False:ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf' if bold else 'C:/Windows/Fonts/segoeui.ttf',sz)
scale=3.7;x0,y0=2535,275;ytop=525
def pt(q):return (65+(q[0]-x0)*scale,160+(ytop-q[1])*scale)
def poly(q,fill,edge='#78908b',width=2):
    for p in b.g.parts(q):
        xy=[pt(a) for a in p.exterior.coords];d.polygon(xy,fill=fill);d.line(xy,fill=edge,width=width)
def line(q,c,w=4):d.line([pt(a) for a in q],fill=c,width=w,joint='curve')
def label(q,t,sz=23,bold=False,c='#173f48'):d.multiline_text(pt(q),t,font=font(sz,bold),fill=c,anchor='mm',align='center',spacing=6)
d.text((50,25),'R25  /  NRT11 and private terminal',font=font(39,True),fill='#173f48')
d.text((50,82),'Measured plan  |  Same east-facing start  |  One shared movement at a time',font=font(25),fill='#5c766d')
poly(b.box(2540,276.6,2890,520),'#d8ddd5')
poly(b.FOOT,'#a7bdbe');label((2814,378),'NRT VIRTUAL\nHEADQUARTERS',29,True)
poly(b.CANOPY,'#c1d6d0');label((2647,332),'CANOPY',24,True)
for col in b.COLS:poly(col,'#294d56')
line([(b.g.SPINE,291),(b.g.SPINE,500)],'#c58f16',6)
for name in ['arrival','departure']:line(b.PROPOSAL[name],'#c58f16',6)
poly(b.HELI_RESERVE,'#c0d4c6');c=pt(b.HELI);r=20*scale
d.ellipse((c[0]-r,c[1]-r,c[0]+r,c[1]+r),outline='#fcfff9',width=5);label(b.HELI,'H',48,True)
label((2675,513),'NRT10',25,True)
poly(b.GA_BOX,'#e7eadb','#fafff7',5)
env=b.box(2667,379.5,2717,445.5);poly(env,'#bcd0bc','#66896e',2)
label((2692,398),'50 m long\n66 m span\nplanning envelope',22,True)
line(b.GA_ROUTE,'#bc8514',5)
line([(2713,409),(2713,416)],'#bc8514',5)
# Show the old box only as a dashed outline for this review, never in scenery.
old=b.b.GA_BOX
for p1,p2 in zip(old.exterior.coords,list(old.exterior.coords)[1:]):
    a=b.np.array(pt(p1));z=b.np.array(pt(p2));dist=b.np.linalg.norm(z-a)
    for t in b.np.arange(0,dist,13):d.line([tuple(a+(z-a)*t/dist),tuple(a+(z-a)*min(dist,t+6)/dist)],fill='#6f827a',width=2)
walk=b.Line(b.WALK).buffer(.8,cap_style=2,join_style=2).union(b.Line(b.GA_WALK).buffer(.8,cap_style=2))
poly(walk,'#fafff8','#287d74',2)
for q in [(2675,454.3),(2693,449.2)]:line([(q[0]-1.4,q[1]),(q[0]+1.4,q[1])],'#b87832',6)
label((2617,443),'NRT11\nApproach-side ID\nand limits',20,True)
line([(2637,438),(2662,414)],'#698a7f',2)
label((2808,472),'North boarding approach\nWalk continues to pad hold point',23)
line([(2753,469),(2693,451)],'#698a7f',2)
label((2625,492),'Main taxi line',20)
label((2822,501),'NRT8 / NRT9\njetway functions retained',22)
line([(2820,487),(2791,431)],'#698a7f',2)
for j in b.EVIDENCE['jetways']:
    poly(b.Line([j['root'],j['base']]).buffer(1.6,cap_style=2),'#eff1e7');poly(b.Point(j['base']).buffer(1.7),'#eff1e7')
label((2646,283),'Canopy forward exit retained',21)
label((2806,304),'Arrival court and service-car route\nremain on the landside',22)
line([(2881,470),(2881,507)],'#173f48',4);poly(b.Polygon([(2879.5,503),(2881,510),(2882.5,503)]),'#173f48','#173f48');label((2881,518),'N',24,True)
d.rectangle((0,1120,1800,1280),fill='#f8faf5')
d.text((50,1145),'54 x 71 m marked bay  /  MAX WINGSPAN 216.5 FT / 66 M  /  MAX LENGTH 164 FT / 50 M',font=font(25,True),fill='#173f48')
d.text((50,1192),'Green rectangle: conservative aircraft envelope. Dashed outline: former small GA bay, removed from scenery.',font=font(23),fill='#5b746a')
d.text((50,1230),'NRT11 departure uses pushback or towing. Planning clearance is not aircraft/add-on operating approval.',font=font(23),fill='#5b746a')
im.save(OUT/'R25_Plan.png')

W,H=842,595;path=PDF/'NRT_R25_Realism_Review.pdf';c=canvas.Canvas(str(path),pagesize=(W,H));c.setTitle('NRT R25 - stock X-Plane realism review');c.setAuthor('NRT scenery development')
ink='#173f48';muted='#526e66';accent='#247e77'
style=ParagraphStyle('text',fontName='Helvetica',fontSize=10.2,leading=14,textColor=HexColor(ink))
small=ParagraphStyle('small',parent=style,fontSize=9,leading=12)
def para(t,x,y,w=746,st=style):
    p=Paragraph(t,st);_,h=p.wrap(w,H);p.drawOn(c,x,y-h);return y-h
def begin(n,title,sub):
    c.setFillColor(HexColor('#f0f3ed'));c.rect(0,0,W,H,fill=1,stroke=0)
    c.setFillColor(HexColor(accent));c.setFont('Helvetica-Bold',10);c.drawString(36,562,'NRT / KIAH / R25 / LOCAL TEST BUILD')
    c.setFillColor(HexColor(ink));c.setFont('Helvetica-Bold',25);c.drawString(36,527,title)
    para(sub,36,510)
    c.setStrokeColor(HexColor('#b8c9bf'));c.line(36,30,W-36,30)
    c.setFont('Helvetica',8);c.setFillColor(HexColor(muted));c.drawString(36,17,'Built for stock X-Plane 12 + MisterX Library + openSAM. No AEP requirement.');c.drawRightString(W-36,17,str(n)+' / 4')
def picture(name,x,y,w,h):c.drawImage(str(OUT/name),x,y,width=w,height=h,preserveAspectRatio=True,anchor='c',mask='auto')
begin(1,'New, maintained, in use','A cohesive finish pass for the headquarters, canopy and arrival court. R24 remains the published version.')
picture('Headquarters_Arrival.png',36,127,770,349)
para('<b>Clean base, selective use.</b> Native new concrete and plain asphalt replace blanket dirt and worn patches. Local wheel tracks and flush drains remain tied to operations.',36,118,365)
para('<b>Material depth.</b> Four-metre facade modules, metal/glass/stone response, standing-seam roofing, softer night glazing, real entrance hardware and sparse stowed equipment.',432,118,374)
para('The images reopen exported meshes. X-Plane wetness, reflected light, pavement FX and animated jetway arms are not simulated in these previews.',36,56,770,small)
c.showPage()
begin(2,'NRT11: use the space, keep the routes','Nose east is retained. The marking layout follows the approach-side placement and direction used at NRT8.')
picture('R25_Plan.png',28,69,524,412)
y=471
for title,body in [
 ('Marked bay','54 m long x 71 m wide. The old narrow box and side-mounted limit strip are removed.'),
 ('Both aircraft limits apply','<b>216.5 ft / 66 m wingspan</b><br/><b>164 ft / 50 m length</b><br/>A wingspan limit alone would admit aircraft that are too long for the tail clearance.'),
 ('Planning clearance','2.83 m minimum to the exported walk during the modelled arrival; 3.33 m minimum to a parked full envelope during G650 canopy movement. Includes a 0.10 m sweep buffer.'),
 ('Operations','Straight final entry; pushback or tow out. Keep the shared approach to one aircraft movement at a time. No random AI fleet is assigned to this length-limited stand.')]:
    y=para('<b>'+title+'</b><br/>'+body,568,y,235)-16
c.showPage()
begin(3,'Jetway entrances that belong to the building','Three rebuilt fixed links and recessed wall collars at NRT8 / NRT9. Animated native jetways stay in the airport file.')
picture('Jetway_Connections.png',36,126,770,349)
para('<b>At the wall:</b> glazing and mullions stop at each opening; sills, jambs and drip edges surround a clear tunnel reveal. New fixed-link bases align within 3.3 cm of the native jetway pivots.',36,118,365)
para('<b>At the apron:</b> flush drainage, a stowed GPU, cone storage and a wall-side fire point add use without putting equipment in the aircraft envelope or pedestrian corridor.',432,118,374)
para('All 119 airport jetway records are unchanged. The image intentionally omits their animated arms; confirm loading and docking in the simulator.',36,56,770,small)
c.showPage()
begin(4,'Review it in the simulator, then release','235 offline checks passed. The build is packaged for your new PC; it has not been installed or pushed to SkunkCrafts.')
left=36;right=444;y=474
for title,body in [
 ('1 / Dry daylight','Use stock X-Plane pavement and disable AEP for the comparison. Check slab scale, quiet surface variation, entrance frames, new ground wording and the old-label cleanup.'),
 ('2 / Wet and overcast','Check native water response and the transition beneath the canopy. No baked puddles or opaque apron overlay is used. Roof shelter behavior remains a runtime check.'),
 ('3 / Dusk and night','Check glass brightness, doorway signs, canopy spill and ramp masts. NRT10 retains ground lighting only and has no new beacon.'),
 ('4 / Operations','Test G650 or Lineage canopy entry and forward exit with NRT11 occupied. Check NRT11 pushback/tow, marshaller stop, terminal/FBO jetways, the crew car and all six independent door controls.'),
 ('5 / Performance and release','Compare frame time and VRAM using the same view and settings. Review screenshots before publishing this revision to the member updater.')]:
    y=para('<b>'+title+'</b><br/>'+body,left,y,370)-15
y=474
for title,body in [
 ('Preserved','Accepted security fencing, one helipad, ground tower, Indoor Parking, MH1/MH2, native vehicle routes and six default-open door controls.'),
 ('Library approach','Laminar public pavement / FX / equipment paths and existing MisterX people / GPU resources. Library contents are referenced rather than copied. No extra animation plugin is introduced.'),
 ('Install the isolated test','Extract the full test ZIP. With X-Plane closed, run <b>Install R25.cmd</b> and select the folder containing X-Plane.exe. The installer verifies hashes, saves scenery_packs.ini and preserves prior scenery folders. Fully relaunch afterward.'),
 ('Sources and limits','The dimensional study uses conservative rectangular footprints and planning wheelbases; it is not live add-on acceptance. Official resources below document the native systems used.')]:
    y=para('<b>'+title+'</b><br/>'+body,right,y,360)-15
for label,url in [('Laminar: Airport Pavement and FX','https://developer.x-plane.com/article/airport-pavement-and-fx/'),('Laminar: X-Plane 12 Material Model','https://developer.x-plane.com/article/the-x-plane-12-material-model/'),('WED: Service Vehicle Networks','https://developer.x-plane.com/manuals/wed/#specifyingservicevehiclenetworks'),('openSAM: project documentation','https://github.com/hotbso/openSAM/blob/main/README.md'),('MisterX: library author page','https://forums.x-plane.org/files/file/28167-misterx-library-and-static-aircraft-extension/')]:
    y=para('<link href="'+url+'" color="#247e77">'+label+'</link>',right,y,360,small)-3
c.save()
(OUT/'Review.txt').write_text('R25 built review: open pdf/NRT_R25_Realism_Review.pdf or R25_Plan.png. The PDF includes actual mesh views, NRT11 dimensions, operations, review sequence and sources. X-Plane runtime acceptance is pending. No public updater change.\n')
print(str(path))
