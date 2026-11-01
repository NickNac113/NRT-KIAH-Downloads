"""Create review-only illustrations, user notes and a portable HTML gallery."""
from common import *
from preview_native import segments
import html, re
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

OUT=ROOT/'output'

def plan():
    apt=ag.parse_apt(PACK/'Earth nav data/apt.dat')
    ev=json.loads((ROOT/'qa/R28_Evidence.json').read_text())
    extent=box(-755,285,45,805)
    fig,ax=plt.subplots(figsize=(16,11.6))
    fig.patch.set_facecolor('#f2f4f2');ax.set_facecolor('#c8d1c0')
    for q in apt:
        if q['code']==110 and q['geom'].intersects(extent):
            ag.draw_geom(ax,smooth_pavement(q),facecolor='#e3e2da',edgecolor='#bcbeb7',linewidth=.35)
    for q in DSF['entities']:
        if q['kind']=='polygon' and 'term_building_' in q['resource'] and q['geom'].intersects(extent):
            ag.draw_geom(ax,q['geom'],facecolor='#aab3b6',edgecolor='#747f85',linewidth=.5)
    for q in apt:
        if q['code']==120 and q.get('geom') is not None and q['geom'].intersects(extent):
            for g,styles in segments(q):
                if any(s in styles for s in ['1','51','2','52']):
                    ag.draw_geom(ax,g,edgecolor='#a98c44',linewidth=.55,alpha=.8)
    ag.draw_geom(ax,B,facecolor='#587581',edgecolor='#244752',linewidth=1.6)
    for f in ev['facades']:
        if f['name'].startswith('bridge_'):
            ag.draw_geom(ax,Polygon(f['points']),facecolor='#94afb7',edgecolor='#3d626d',linewidth=.5)
    for lane in ev['taxi']:
        g=LineString(lane['points']);ag.draw_geom(ax,g,edgecolor='#6b5726',linewidth=3.7)
        ag.draw_geom(ax,g,edgecolor='#efbd3f',linewidth=2.5)
    for q in apt:
        if q['code']==120 and q['lines'][0].startswith('120 R28 B North R1 '):
            for g,s in segments(q):
                ag.draw_geom(ax,g,edgecolor='#6b5726',linewidth=3.7)
                ag.draw_geom(ax,g,edgecolor='#efbd3f',linewidth=2.5)
    for q in STARTS:
        x,y=q['geom'].coords[0]
        ax.scatter([x],[y],s=6,c='#244752',zorder=6)
        a=math.radians(q['heading']);dx=-math.sin(a)*12;dy=-math.cos(a)*12
        ax.annotate(q['name'].removeprefix('Gate '),(x,y),xytext=(x+dx,y+dy),
                    textcoords='data',fontsize=8.8,color='#183942',ha='center',va='center',
                    bbox=dict(boxstyle='round,pad=.18',fc='#f2f4ed',ec='none',alpha=.95),zorder=7)
    for x,y,txt in [(-679,560,'ND'),(-375,568,'R1'),(-154,630,'NG'),(-550,734,'NB'),(-375,381,'TERMINAL B\nNORTH')]:
        ax.text(x,y,txt,ha='center',va='center',fontsize=13 if len(txt)<4 else 15,
                weight='bold',color='#fff' if 'TERMINAL' in txt else '#193c46',
                bbox=None if 'TERMINAL' in txt else dict(boxstyle='round,pad=.3',fc='#f2f4ed',ec='none'))
    ax.annotate('Smooth R1 entry / exit\nPaint follows the aircraft route',xy=(-372,703),xytext=(-365,774),ha='center',
                fontsize=11,color='#244752',arrowprops=dict(arrowstyle='-',color='#244752',lw=1))
    ax.annotate('Existing C-side lane\nretained',xy=(-102,580),xytext=(8,650),ha='right',fontsize=10.5,
                color='#4b5d63',arrowprops=dict(arrowstyle='-',color='#4b5d63',lw=1))
    ax.annotate('One painted spine\nper retained B route',xy=(-644,470),xytext=(-735,332),ha='left',fontsize=10.5,
                color='#244752',arrowprops=dict(arrowstyle='-',color='#244752',lw=1))
    ax.text(-580,302,'All 22 gate starts and animated jetway positions retained.',fontsize=11,color='#244752')
    ax.annotate('',xy=(17,782),xytext=(17,746),arrowprops=dict(arrowstyle='-|>',lw=1.8,color='#244752'))
    ax.text(17,790,'N',ha='center',fontsize=12,weight='bold',color='#244752')
    ax.plot([-735,-685],[785,785],color='#244752',lw=3)
    ax.text(-710,794,'50 m',ha='center',fontsize=10,color='#244752')
    ax.set(xlim=(-755,45),ylim=(285,805));ax.set_aspect('equal');ax.set_xticks([]);ax.set_yticks([])
    for s in ax.spines.values():s.set_color('#9ca9a5')
    fig.suptitle('TERMINAL B  /  TAXI GUIDANCE REFINEMENT',x=.055,y=.965,ha='left',fontsize=22,weight='bold',color='#173b46')
    fig.text(.055,.925,'R28  ·  Model coordinates  ·  North up  ·  Review plan, not a navigation chart',fontsize=12,color='#52666d')
    fig.legend(handles=[Patch(facecolor='#587581',label='Refined B terminal'),Line2D([0],[0],color='#efbd3f',lw=3,label='B taxi guidance'),
                        Line2D([0],[0],color='#a98c44',lw=1,label='Existing airport guidance')],loc='lower left',bbox_to_anchor=(.05,.045),ncol=3,frameon=False,fontsize=11)
    fig.text(.055,.025,'The supplied map guides the lane arrangement. Existing scenery coordinates remain the geometric baseline.',fontsize=10,color='#52666d')
    fig.subplots_adjust(left=.05,right=.97,bottom=.12,top=.89)
    fig.savefig(OUT/'Terminal_B_Taxi_Plan.png',dpi=160);plt.close(fig)

def review():
    val=json.loads((ROOT/'qa/Validation.json').read_text())
    assert val['status']=='PASS'
    body='''
<header><div class="eyebrow">KIAH · R28 · LOCAL REVIEW BUILD</div><h1>Terminal B, brought into the airport.</h1>
<p class="lead">Matching terminal materials, readable taxi guidance and the familiar glass corridors with passengers visible inside.</p>
<div class="chips"><span>22 B North gates retained</span><span>Native X-Plane terminal kit</span><span>No AEP required</span></div></header>
<nav><a href="#appearance">Appearance</a><a href="#taxi">Taxi plan</a><a href="#checks">Checks & testing</a><a href="#sources">Sources & assets</a><a href="Review.txt">Plain-text copy</a></nav>
<main><section id="appearance"><h2>The visual change</h2><p>The flat custom B shell has been replaced with the same X-Plane terminal-kit family already used around the neighboring concourses. The approved U-shaped footprint is retained. Ground-level service windows, upper glass, native roof materials, 12 HVAC units and six skylights give the building the same visual language as its surroundings.</p>
<figure><a href="Terminal_B_Overview.png"><img src="Terminal_B_Overview.png" alt="Native-asset overview of the refined Terminal B and surrounding concourse"></a><figcaption>Exported-asset preview: B North in the foreground with neighboring terminal context. Click any image to open it full size.</figcaption></figure>
<div class="two"><figure><a href="Terminal_B_Gate_Detail.png"><img loading="lazy" src="Terminal_B_Gate_Detail.png" alt="Glass fixed bridges and retained gate signs at Terminal B"></a><figcaption>22 fixed bridge tunnels now use the matching glass bridge kit. Existing supports, pivot connectors and animated jetways stay at their established locations; gate plaques rise clear of the taller tunnel roof.</figcaption></figure>
<figure><a href="Terminal_B_Passenger_Windows.png"><img loading="lazy" src="Terminal_B_Passenger_Windows.png" alt="Terminal windows showing the stock passenger, seating and display artwork"></a><figcaption>Passenger silhouettes, seating and displays come from the stock terminal artwork. These are painted interior imagery, not animated pedestrians.</figcaption></figure></div>
<figure><a href="Terminal_B_Evening.png"><img loading="lazy" src="Terminal_B_Evening.png" alt="Evening review of native illuminated terminal windows"></a><figcaption>Evening material preview using the native illuminated texture. This is a rendered review image, not an X-Plane screenshot.</figcaption></figure>
<p class="note">The previews use the exported geometry and installed stock art. Facade segment selection approximates X-Plane; pavement appearance, line widths and lighting are review approximations. Weather, terrain elevation, moving traffic and live jetway docking are not simulated here.</p></section>
<section id="taxi"><h2>Clearer ND, R1 and NG guidance</h2><p>The supplied map was compared with the existing aircraft network. Redundant parallel B-side branches have been removed. ND and the B-side NG spine now follow the retained aircraft routing, and R1 has smooth arrival and departure curves at NB. The adjacent C-side lane remains in place.</p>
<figure><a href="Terminal_B_Taxi_Plan.png"><img loading="lazy" src="Terminal_B_Taxi_Plan.png" alt="North-up plan of Terminal B with ND, R1, NG and NB taxi lanes and 22 retained gates"></a><figcaption>Model plan, not an operational chart. The supplied screenshot establishes the arrangement; it does not provide survey control or confirm independent use of parallel routes.</figcaption></figure>
<p>The three gray strokes shown in the map's central alley have not been treated as three separate aircraft lanes. All 22 existing B North starts are retained, including B5 and B17, whose labels are not visible on the supplied map. Gate-by-gate numbering should be checked against a current operational chart before any future renumbering.</p></section>
<section id="checks"><h2>Built and checked; ready for local testing</h2>
<div class="stats"><div><strong>267 / 267</strong><span>offline checks passed</span></div><div><strong>249</strong><span>predecessor files unchanged</span></div><div><strong>&lt; 0.09 m</strong><span>authored footprint boundary change</span></div></div>
<p>The scenery binary was compiled and read back successfully. Taxi paint aligns with the retained route graph; the smooth R1 curves stay within 8 cm of its sampled routing. All gate starts, native animated jetways, OpenSAM configuration, vehicle-route records and pavement definitions were preserved. The largest binary coordinate-encoding shift is approximately 10 cm.</p>
<p>B South, neighboring terminal placements and the NRT campus have not been redesigned. The original B shell remains as an unused asset in the package for traceability, but its placement has been removed.</p>
<h3>Suggested simulator review</h3><ol><li>Load B North in daylight and inspect the ground/upper facade joins, roof junctions and glass corridors from ramp level.</li><li>Check arrival and departure through ND, R1 and NG at slow taxi speed, including the NB connections and wingtip clearance with neighboring stands occupied.</li><li>Dock and undock at B3, B8, B15 and B22, then check the remaining jetways. The animated jetway positions were preserved, but live docking still needs verification.</li><li>Check dusk/night windows and the apron in rain. Check traffic movement and performance during a normal airport session.</li></ol>
<p class="note">Offline geometry checks are not aircraft-specific swept-path validation or simulator acceptance. Installed and public R27 are unchanged. R28 has not been installed or pushed to SkunkCrafts.</p>
<h3>Test package</h3><p><a href="../NRT_KIAH_R28_Review.zip">Download the local R28 review ZIP</a> · <a href="../qa/Validation.json">Detailed check results</a> · <a href="../qa/Preview_Method.json">Preview method</a></p>
<p>The archive includes the cumulative scenery folder, these previews and manual test-install notes. Use only one cumulative NRT KIAH revision at a time. The new terminal references X-Plane's native assets; the existing campus still requires MisterX Library, openSAM_Library and openSAM for its animated features.</p></section>
<section id="sources"><h2>Sources and asset choices</h2>
<table><thead><tr><th>Source / asset</th><th>Use in this revision</th></tr></thead><tbody>
<tr><td>User-supplied updated airport map</td><td>ND / R1 / NG / NB arrangement, terminal shape and visible gate labels. Used as a layout reference, not georeferenced survey data.</td></tr>
<tr><td>Installed airport scenery and retained R27 package</td><td>Measured geometry, existing aircraft network, bridge pivots, neighboring material choices and cumulative campus baseline.</td></tr>
<tr><td><a href="https://www.fly2houston.com/airport-business/newsroom/press-releases/item/united-airlines-terminal-b-north-opens-at-iah/">Houston Airports: Terminal B North opening</a></td><td>The October 21, 2026 announcement confirms 22 mainline gates at B North. This supports retaining the 22-gate set; it does not verify each stand label.</td></tr>
<tr><td><a href="https://developer.x-plane.com/article/terminal-kit/">Laminar Research: Terminal Kit</a></td><td>Native ground and upper facades, fixed glass bridges, roof equipment and skylights. Logical building sections and matching anchors follow the kit's construction method.</td></tr>
<tr><td><a href="https://developer.x-plane.com/article/facade-overview/">Laminar Research: Facade Overview</a></td><td>Facade rings/chains, winding and object format behavior.</td></tr>
<tr><td>Ground_01 / Levels_02</td><td>Service frontage, upper terminal glass and stock interior passenger imagery. Native normal, material and illuminated textures are resolved by X-Plane.</td></tr>
<tr><td>term_bridge_01 / roof_elements_01 / roof_long_skylight_01</td><td>Matching glass tunnels, HVAC and skylights. No third-party replacement textures added.</td></tr>
<tr><td>MisterX / openSAM</td><td>Existing dependencies and features are retained. Native terminal assets were selected for this pass because they match the adjacent terminals. No AEP-only resource is introduced.</td></tr>
</tbody></table>
<p>Laminar library textures are referenced in the scenery rather than copied into it. Atlas inspection images and authoring intermediates are excluded from the review archive. Source history remains local/private.</p></section></main>
<footer>R28 · 2026-11-01 · Review build · Simulator acceptance pending</footer>'''
    style='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f1f3f2;color:#203840;font:16px/1.6 Segoe UI,Arial,sans-serif}header,main,nav,footer{max-width:1320px;margin:auto;padding:28px 36px}header{padding-top:56px}h1{font-size:clamp(30px,4vw,52px);line-height:1.12;margin:12px 0 20px;max-width:950px;letter-spacing:-1px}h2{font-size:29px;line-height:1.2}h3{font-size:20px}.eyebrow{letter-spacing:2px;font-size:12px;font-weight:700;color:#51717a}.lead{max-width:850px;font-size:21px;color:#526a70}.chips{display:flex;gap:10px;flex-wrap:wrap}.chips span{background:#dce7e4;padding:7px 12px;border-radius:4px;font-size:14px}nav{border-block:1px solid #ccd8d5;display:flex;gap:24px;flex-wrap:wrap;padding-block:15px}a{color:#176579;text-underline-offset:3px}section{padding:15px 0 40px;scroll-margin-top:15px}p{max-width:1040px}figure{margin:24px 0 34px}img{display:block;width:100%;height:auto;border:1px solid #c8d3d1;background:#d9dfdc}figcaption{font-size:14px;color:#54676d;margin-top:9px}.two{display:grid;grid-template-columns:1fr 1fr;gap:24px}.note{background:#e1e8e5;border-left:4px solid #728f89;padding:15px 20px;font-size:14px}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin:25px 0}.stats div{background:#fff;padding:20px;border:1px solid #d4dfda}.stats strong{display:block;font-size:30px;color:#235665}.stats span{font-size:14px;color:#62736f}table{border-collapse:collapse;width:100%;background:#fff}th,td{text-align:left;padding:15px;border-bottom:1px solid #d8e1dd;vertical-align:top}th{background:#dfe8e4}td:first-child{width:33%;font-weight:600}ol{max-width:1000px;padding-left:25px}li{margin:10px 0}footer{border-top:1px solid #ccd8d5;color:#637772;font-size:13px}@media(max-width:700px){header,main,nav,footer{padding-inline:18px}.two,.stats{grid-template-columns:1fr}td,th{padding:10px;font-size:14px}}'''
    (OUT/'Review.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>KIAH R28 · Terminal B refinement</title><style>'+style+'</style></head><body>'+body+'</body></html>',encoding='utf-8')
    text='''KIAH R28 - TERMINAL B REFINEMENT
2026-11-01 | Local review build | Not installed or published

WHAT CHANGED
Terminal B North now uses the stock X-Plane terminal kit already used around
neighboring concourses: service windows below, terminal glass above, painted
interior passengers, illuminated windows, matching glass fixed bridges,
12 HVAC units and six skylights. The existing U-shaped footprint is retained.
The 22 animated jetways and gate starts remain at their established locations.
Painted passengers are texture imagery, not animated people.

ND and the B-side NG spine now align with the retained aircraft network.
Redundant parallel B-side branches are removed. R1 has smooth entry/exit
curves at NB. The neighboring C-side route is retained. The map's three gray
central strokes have not been interpreted as three independent aircraft lanes.
B5 and B17 remain because an absent map label is not proof of a closed stand.

CHECKS
267/267 offline checks pass. The DSF compiled and read back successfully.
249 predecessor files remain byte-identical; the authored terminal footprint
boundary changes by less than 9 cm. The maximum binary coordinate encoding
shift is approximately 10 cm. R1 paint follows the sampled aircraft graph
within 8 cm. All starts, native animated jetways, OpenSAM configuration,
vehicle route records and pavement definitions are preserved.

REVIEW IMAGES (same folder)
Terminal_B_Overview.png
Terminal_B_Gate_Detail.png
Terminal_B_Passenger_Windows.png
Terminal_B_Evening.png
Terminal_B_Taxi_Plan.png

These are exported-asset previews, not X-Plane screenshots. Facade segment
selection, ground appearance, line widths and lighting are approximations.
No weather, terrain, moving traffic or live jetway docking is simulated.
Offline checks do not establish aircraft-specific swept paths or runtime
acceptance. B South, A/C/D and the NRT campus have not been redesigned.

SIMULATOR REVIEW
1. Inspect facade joins, roofs and fixed glass corridors in daylight.
2. Taxi ND/R1/NG and the NB connections slowly; check occupied-stand clearance.
3. Dock/undock at B3, B8, B15 and B22, then check the remaining gates.
4. Inspect night illumination and rain, traffic movement and performance.

DEPENDENCIES
X-Plane 12; existing MisterX Library, openSAM_Library and openSAM campus
dependencies retained. No AEP required. Stock Laminar art is referenced, not
copied. Raw texture inspection images are excluded from the archive.

SOURCES
User-supplied updated airport map; installed scenery and retained R27 geometry.
Houston Airports (22 North mainline gates, October 21, 2026):
https://www.fly2houston.com/airport-business/newsroom/press-releases/item/united-airlines-terminal-b-north-opens-at-iah/
Laminar Research Terminal Kit:
https://developer.x-plane.com/article/terminal-kit/
Laminar Research Facade Overview:
https://developer.x-plane.com/article/facade-overview/

Current installed/public R27 remains unchanged. R28 is ready for review and
later local simulator testing; it has not been installed or sent to SkunkCrafts.
'''
    (OUT/'Review.txt').write_text(text,encoding='utf-8')
    readme='''KIAH NRT R28 - TERMINAL B REFINEMENT
2026-11-01

CURRENT STATUS: Local review/test build. Not installed or published.
This is a cumulative successor to R27. Earlier README files describe historic
revisions; this file defines the status of the R28 review package.

CHANGES
- Native X-Plane terminal glass, interior passenger artwork and matching roofs.
- 22 matching fixed glass corridors; existing animated jetway positions retained.
- 12 roof HVAC units, six skylights; U-shaped B North footprint retained.
- ND/NG paint aligned to aircraft network; duplicate B-side branches removed.
- Smooth R1 arrival/departure paint at NB.
- No redesign of B South, neighboring terminal placements or NRT campus.

267 offline checks passed. Simulator testing and live jetway docking are pending.
No AEP dependency. Existing MisterX Library, openSAM_Library and openSAM
requirements remain. Native library assets are referenced, not bundled.

MANUAL TEST INSTALL (WHEN READY)
1. Fully exit X-Plane. Preserve your current scenery folder and scenery_packs.ini.
2. Copy KIAH_NRT_R28_Terminal_B_R25 into X-Plane 12/Custom Scenery/.
3. In scenery_packs.ini enable this folder at the same priority as your current
   cumulative NRT KIAH revision. Disable the previous cumulative revision and any
   NRT_KIAH_Campus duplicate. Do not run two cumulative revisions together.
4. Keep required libraries enabled. Launch X-Plane, load KIAH and follow the
   review sequence in Review/Review.txt.
5. To revert, exit X-Plane, disable R28 and restore the previous scenery entry.

This review folder intentionally has no new updater configuration. Do not
overwrite your member install with this review package. Publication will be a
separate release after simulator review.
'''
    (PACK/'README_R28.txt').write_text(readme,encoding='utf-8')
    (ROOT/'STATUS.txt').write_text('R28 built and offline validated (267/267).\nReview package ready.\nRuntime acceptance pending.\nNot installed. Not published.\nProtected baseline: R27.\n',encoding='utf-8')

if __name__=='__main__':
    plan();review()
    print(str(OUT/'Review.html'))
