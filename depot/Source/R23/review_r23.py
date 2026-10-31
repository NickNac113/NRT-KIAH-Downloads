"""Dimensioned review plots and portable test notes for R23."""
from pathlib import Path
import importlib.util,sys,json,math
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('build',ROOT/'source/build_r23.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
from PIL import Image, ImageDraw, ImageFont, ImageColor
OUT=b.OUT;PACK=b.PACK
V=json.loads((OUT/'Validation.json').read_text())
class Plot:
    def __init__(self,bounds,title,w=1600,h=1200):
        self.im=Image.new('RGB',(w,h),'#f1f4ef');self.d=ImageDraw.Draw(self.im);self.bounds=bounds
        x0,y0,x1,y1=bounds;self.scale=min((w-160)/(x1-x0),(h-240)/(y1-y0));self.left=(w-(x1-x0)*self.scale)/2;self.top=125
        self.d.text((45,30),title,font=ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf',32),fill='#163d47')
        self.d.text((45,80),'NORTH UP / Dimensions in metres / Offline scenery plan',font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',19),fill='#587078')
    def point(self,p):return (self.left+(p[0]-self.bounds[0])*self.scale,self.top+(self.bounds[3]-p[1])*self.scale)
    def area(self,geom,color,edge='#7e8d89',alpha=1,lw=1):
        layer=Image.new('RGBA',self.im.size);d=ImageDraw.Draw(layer)
        for p in b.g.parts(geom.intersection(b.box(*self.bounds))):
            pts=[self.point(q) for q in p.exterior.coords];fill=None if color=='none' else (*ImageColor.getrgb(color),int(255*alpha));d.polygon(pts,fill=fill,outline=(*ImageColor.getrgb(edge),255),width=lw)
        self.im.paste(layer,(0,0),layer);self.d=ImageDraw.Draw(self.im)
    def line(self,pts,color,lw=2):self.d.line([self.point(p) for p in pts],fill=color,width=lw)
    def text(self,x,y,text,size=18,color='#183d46'):
        self.d.multiline_text(self.point((x,y)),text,font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',size),fill=color,anchor='mm',align='center',spacing=4)
    def arrow(self,a,c,color):
        self.line([a,c],color,4);v=b.np.array(c)-a;v=v/b.np.linalg.norm(v);r=b.np.array([v[1],-v[0]])
        self.d.polygon([self.point(p) for p in [c,b.np.array(c)-v*4+r*2,b.np.array(c)-v*4-r*2]],fill=color)
    def save(self,name,note):
        self.d.multiline_text((45,self.im.height-76),note,font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',18),fill='#415d63',spacing=5);self.im.save(OUT/name)
p=Plot((2398,266,2897,601),'R23 | Jet Center and separate passenger-car access')
p.area(b.box(2412,276.6,2882,590),'#d6d9d2')
for geom,name in [(b.box(2415,490,2512,590),'MH1'),(b.box(2446,434,2512,488),'MH2'),(b.box(2434,284,2512,434),'PRIVATE\nHANGAR')]:
    p.area(geom,'#597079');c=geom.centroid;p.text(c.x,c.y,name,23,'white')
p.area(b.FOOT,'#204c58');p.text(2798,376,'NRT JET CENTER / FBO',23,'white')
p.area(b.CANOPY,'#7b9c98',alpha=.55);p.text(2647,320,'COVERED\nARRIVAL',17)
p.line([(b.g.SPINE,280),(b.g.SPINE,590)],'#c69319',4)
for y in [359,461,540]:p.line([(2512,y),(2558,y)],'#c69319',3)
p.line(b.APPROACH,'#237a9c',4);p.arrow((2648,383),(2648,357),'#237a9c')
p.text(2605,472,'Side-entry\napproach',19,'#237a9c')
p.area(b.box(2652,457,2698,503),'none','#6d8780');p.area(b.Point(*b.HELI).buffer(20),'#a6b4a6','white',lw=3);p.text(*b.HELI,'H',42,'white');p.text(2675,446,'NRT10 - single pad',17)
p.area(b.box(2692,292,2735,330),'#7d8987');p.area(b.g.MEDIAN,'#839974')
p.line(b.VEHICLE,'#efaf41',3);p.line([(2730,310),(2744,310)],'#efaf41',3);p.text(2810,305,'Car park / delivery access',19)
p.line([(2692,276.6),(2692,291.9)],'#a05d58',3);p.line([(2412,276.6),(2724.66,276.6)],'#a05d58',2)
for x,y in [[2784.14,426.06],[2791.14,430.06],[2860.53,427.06]]:p.area(b.box(x-2,y-2,x+2,y+2),'#607b8b')
p.text(2815,442,'NRT8 single / NRT9 dual jetways retained',17);p.arrow((2860,545),(2860,574),'#204c58');p.text(2860,583,'N',27)
p.save('Campus_Plan.png','Blue route: arrival/tow guide. Gold car route: native service routing. Stand taxi paint remains detached.\nAircraft steering, OpenSAM operation and terrain appearance require the next simulator test.')

p=Plot((2614,280,2694,389),'R23 | Covered side-entry alignment',1200,1400)
p.area(b.CANOPY,'#d2dfd9');p.area(b.FOOT,'#355963')
for c in b.COLS:p.area(c,'#213e44')
colors=['#ae934f','#6389a0','#83a087']
for (name,d),c in zip(V['measurements']['parked_aircraft'].items(),colors):
    p.area(b.box(*d['parked_envelope']),c,edge=c,alpha=.25,lw=3)
p.line([(2648,378),(2648,303)],'#c69624',3);p.arrow((2648,372),(2648,362),'#237a9c');p.text(2648,383,'ENTER FROM NORTH / TOW BACK OUT',21)
p.line([(2649.66,303.86),b.DOOR],'#bd7557',4);p.text(2660,309,'Left-door walk\nto terminal',19,'#91583e')
p.area(b.Point(*b.DOOR).buffer(.5),'#e3c49d');p.area(b.Point(2648,286).buffer(.5),'#457f8c');p.text(2660,286,'OpenSAM marshaller',19)
p.text(*b.NG,'+',26);p.text(2636,300,'Nosewheel stop',19);p.text(2682,320,'TERMINAL\nWING',22,'white');p.text(2648,323,'BBJ2 / Lineage / G650\nconservative parked envelopes',19)
p.text(2648,352,'14 m minimum structure clearance',20)
p.save('Canopy_Plan.png','Door alignment uses the supplied Lineage log. Other add-ons may need a small stop adjustment.\nBBJ2 remains tow-in / tow-out; reverse departure is required. No automatic tug control is supplied.')

guide='''NRT KIAH R23 - Jet Center refinement (R19)

CHANGES
One cohesive FBO/private terminal exterior, matching canopy, glazed bays, stone
base, metal roof ribs, facade shades, passenger portals and photometric lights.
The canopy stand now faces south, entering from the north side, so the left
passenger door faces the doorway under the canopy. NRT CANOPY is a main start.
A real openSAM marshaller placement and detached native yellow guidance serve it.
Use tow-in / tow-out for the BBJ2. All departures must back out to the north;
there is no through exit across the south perimeter fence.

One 40 m native helipad remains, named NRT10, with its existing ground-level
lighting and a 46 m reserve outline. NRT10B and its start/paint were removed.
Its internal native helipad designator is H2; its stand name and ground label
remain NRT10. The airport's unrelated existing H1 is retained. This also removes
the old NRT-prefixed helipad designators associated with 00N warnings in the log.
Retired stand-label fragments, overlapping ground paint and the court fence were
cleared. The private-hangar ground label now reads from the approaching apron.
Native weather-aware concrete, concrete seams and a drainage detail replace the
old pad hole and define the canopy surface. No flat weather-obscuring apron mesh
was added. A native crew car starts in the existing car-park aisle, follows a
separate one-way arrival loop around the median and visits the passenger curb.
The delivery bay, tree, planting, flagpole, cargo area and maintenance layout stay.

OPENsam / JETWAYS
Your supplied scenery_packs.ini has the correct final slash. Your supplied log
shows X-Plane loaded NRT after OpenSAM's startup scan, but that scan contains no
NRT XML/apt.dat read. First-launch discovery timing is a hypothesis, not a proven
cause. The restart test was deferred at your request.
R23 preserves all 119 native airport jetway rows and all eight existing door
controls. It does not replace plugin binaries or change plugin preferences.
The installer writes the selected NRT entry before the next simulator launch,
with a final slash and above other scenery. It disables old NRT selections and
backs up the original INI; their folders are preserved.

INSTALL ON THE GAMING PC
Extract the ZIP fully. Close X-Plane. Run Install R23.cmd and enter the folder
containing X-Plane.exe. Keep MisterX Library, OpenSAM and openSAM_Library installed.
The test build is selected under its own versioned folder. The existing stable
NRT_KIAH_Campus folder and public updater release are preserved.
After installing, launch X-Plane fresh and load KIAH. Run Check OpenSAM.cmd after
that session to inspect NRT discovery in Log.txt. The checker changes no files.
Rollback: close X-Plane and restore the scenery_packs.before-NRT-R23-*.ini backup
from Custom Scenery as scenery_packs.ini.

SIMULATOR ACCEPTANCE CHECK
1. At the hangars, verify eight Close controls appear when their objects are
   visible. Test MH1 outer/middle/tail, MH2, private hangar and three garage doors.
2. Check terminal B and the FBO animated jetways: NRT8 single, NRT9 dual. Fixed
   rotundas alone do not count as a pass. If still absent, retain the new Log.txt
   and the read-only checker's output for diagnosis.
3. Taxi or tow a Lineage south from the canopy approach with its beacon on.
   For testing without a preceding flight, use OpenSAM Activate or select
   NRT CANOPY in its stand menu. Confirm marshalling, stop point and L1 alignment.
   G650/BBJ2 door positions vary by add-on; the supplied Lineage log is the datum.
4. Inspect one NRT10 helipad, absence of old labels/paint shards, corrected
   private-hangar label, and the unobstructed passenger court.
5. Watch the crew car from the car-park aisle to the curb and back. Inspect wet
   pavement and night lighting. No runtime behavior has been verified here.

OFFLINE CHECKS
Compiled DSF was roundtripped and its placement drift measured below 0.25 m.
All material/library references and OBJ draw ranges resolve. All three planning
aircraft boxes fit under the roof; BBJ2 minimum roof gap is 1.5 m and its sampled
approach-box gap to fixed structures is 5.45 m. These are geometric checks,
not a validation of an aircraft's steering model or tug behavior.
Source, predecessor hashes, geometry validation and previews remain in the R23
workspace. No simulator was launched or installed during authoring. No public
depot update is included in this test ZIP.
'''
(PACK/'README_R23.txt').write_text(guide,encoding='utf-8');(OUT/'Install_and_Test.txt').write_text(guide,encoding='utf-8')
diagnosis=dict(input_ini_entry='SCENERY_PACK Custom Scenery/NRT_KIAH_Campus/',ini_entry_correct=True,openSAM_version='5.5.0-beta-3 d45807f',observed='NRT omitted from OpenSAM startup XML/apt scan; X-Plane subsequently loaded its DSFs and starts.',suspected='First-launch scenery discovery timing; not proven.',restart_test='User will test later',configuration=dict(door_controls=8,native_jetway_records=119),r23_action='Retain configurations; select explicit versioned INI entry before launch; add read-only diagnostic.',runtime_fixed=False)
(OUT/'OpenSAM_Diagnosis.json').write_text(json.dumps(diagnosis,indent=2))
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>NRT KIAH R23</title><style>body{margin:0;background:#eff3ed;color:#183c46;font:18px/1.6 system-ui}main{max-width:1380px;margin:auto;padding:35px}h1{font-size:48px;line-height:1.12}img{width:100%;margin:18px 0;border-radius:8px}.note{border-left:4px solid #b88736;background:#e9e3d5;padding:18px}nav{display:flex;gap:16px;flex-wrap:wrap}nav a{background:#204d58;color:white;padding:10px 18px;text-decoration:none;border-radius:5px}a{color:#08767a}table{border-collapse:collapse;width:100%}td,th{text-align:left;border-bottom:1px solid #ccd9d0;padding:10px}small{color:#516e70}h2{margin-top:44px}</style><main><p>NRT / KIAH / R23 TEST</p><h1>A connected Jet Center.<br>A covered side arrival.</h1><p>The private wing, FBO and aircraft canopy now share one exterior design. The canopy start faces south, placing the aircraft’s left passenger door toward the terminal doorway. The parking-lot car route stays on the public side.</p><nav><a href="../NRT_KIAH_R23_Test.zip">Download R23 test</a><a href="Install_and_Test.txt">Install and simulator checks</a><a href="Validation.json">Export validation</a><a href="OpenSAM_Diagnosis.json">OpenSAM findings</a></nav><p class="note"><b>Built and checked offline; simulator test pending.</b> Your INI entry is correct. The supplied log shows OpenSAM did not read NRT during startup, though X-Plane loaded it later. The restart check is deferred. R23 retains all eight door controls and 119 native jetway records; it does not claim the runtime issue is resolved.</p><img src="Canopy_Export.png" alt="Actual exported Jet Center and canopy geometry with south-facing aircraft reference"><p>The BBJ2 reference fits beneath the 14 m minimum structure height, including its tail. Use tow-in / tow-out for the BBJ2 and reverse departure to the north. The doorway alignment is based on the supplied Lineage log; other add-ons may need a small stop adjustment.</p><img src="Canopy_Plan.png" alt="Dimensioned canopy plan with aircraft boxes and passenger-door alignment"><h2>One campus, one helipad</h2><img src="Campus_Plan.png" alt="North-up R23 plan showing one helipad and separate vehicle access"><p>NRT10 is the single retained 40 m pad with ground-level lighting. Old pad paint, obsolete stand fragments and the fence crossing the arrival court are removed. The private-hangar ground label now faces the approaching apron. The 14 main NRT starts remain.</p><h2>The passenger arrival court</h2><img src="Arrival_Export.png" alt="Cohesive glazed FBO exterior beside landscaped passenger drop-off"><p>Original tiled material maps, glazing, stone base, bronze accents, roof ribs, drainage and photometric entrance lighting replace the abrupt old/new building joint. Native X-Plane pavement and surface details retain weather response. A crew car has a native route from the car-park aisle around the median to the passenger curb; the delivery bay remains separate.</p><table><tr><th>Offline geometry</th><th>Result</th></tr><tr><td>BBJ2 minimum roof clearance</td><td>1.5 m</td></tr><tr><td>Sampled BBJ2 approach box to fixed structures</td><td>5.45 m minimum</td></tr><tr><td>Lineage / G650 roof gaps</td><td>3.43 m / 6.18 m</td></tr><tr><td>Door controls / native jetways</td><td>8 / 119 preserved</td></tr><tr><td>Retained NRT helipads / main starts</td><td>1 / 14</td></tr></table><p><small>The images reopen exported OBJ8 geometry. Aircraft, vegetation and ground context are schematic; native jetway animation, OpenSAM marshalling, weather shaders and moving vehicles are not simulated in these renders. Geometry checks do not establish aircraft steering or runtime acceptance.</small></p><p><small>References: <a href="https://developer.x-plane.com/article/airport-data-apt-dat-12-00-file-format-specification/">Laminar airport/service-route format</a>, <a href="https://github.com/hotbso/openSAM/blob/d45807f/README.md">OpenSAM activation</a>, <a href="https://github.com/hotbso/openSAM/blob/d45807f/src/scenery.cpp">OpenSAM scenery discovery</a>.</small></p></main></html>'''
(OUT/'Review.html').write_text(html,encoding='utf-8')
print('R23 review plans and notes written')
