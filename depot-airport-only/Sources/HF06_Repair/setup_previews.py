import pathlib,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1];PREV=ROOT.parent/'KIAH_R03_HF05_Repair';W=ROOT/'work'
for name in ('scene-hf03.json','stock-sign-atlas.png','stock-dir-atlas.png'):
    shutil.copy2(PREV/'work'/name,W/name)
s=(PREV/'work/prepare_previews.py').read_text()
s=s.replace('KIAH_2026-10-24_Review_R03_HF05','KIAH_2026-10-24_Review_R03_HF06')
s=s.replace("plan,oldapt,before=pickle.loads((ROOT/'work/current.pkl').read_bytes())", "plan,oldapt,tiles=pickle.loads((ROOT/'work/inventory.pkl').read_bytes());before=tiles[0][1]")
s=s.replace('from hf05_common import SOURCE, visible_surfaces',"SOURCE=pathlib.Path(r'C:\\Users\\Nick\\Documents\\Codex\\2026-10-24\\cou\\outputs\\KIAH_2026-10-24_Review_R03_HF05')")
s=s.replace('crop=box(-750,300,30,850)',"""crop=unary_union([box(-750,300,30,850),box(275,545,340,625)])
def visible_surfaces(apt):
    covered=Polygon();out=[]
    for i,a in enumerate(apt):
        if a['code'] not in (100,110):continue
        g=a['geom'] if a['code']==100 else smooth_pavement(a)
        if not g.intersects(crop):continue
        surf=int(a['parts'][1])%100
        if a['code']==110 and surf in (0,3,4,5,13,15):continue
        clipped=g.intersection(crop);out.append((i,surf,clipped.difference(covered)));covered=covered.union(clipped)
    return out""")
s=s.replace("[('After',STAGE,before,parse_apt(STAGE/'Earth nav data/apt.dat'))]", "[('Before',SOURCE,before,oldapt),('After',STAGE,before,parse_apt(STAGE/'Earth nav data/apt.dat'))]")
(W/'prepare_previews.py').write_text(s)
s=(PREV/'work/render_hf05.py').read_text().replace('KIAH_2026-10-24_Review_R03_HF05','KIAH_2026-10-24_Review_R03_HF06')
s=s.replace("OUT=ROOT/'previews-final'", "BEFORE=pathlib.Path(r'C:\\Users\\Nick\\Documents\\Codex\\2026-10-24\\cou\\outputs\\KIAH_2026-10-24_Review_R03_HF05')\nOUT=ROOT/'previews-final'")
s=s.replace("for tag,pack in [('After',AFTER)]", "for tag,pack in [('Before',BEFORE),('After',AFTER)]")
start=s.index('views=[');end=s.index('\nrequested=',start)
s=s[:start]+"""views=[
 ('01_D5_Before','Before',(320,553,11),(311.2,569.8,5),13,1400,1000),
 ('02_D5_After','After',(320,553,11),(311.2,569.8,5),13,1400,1000),
 ('04_B_North_After','After',(-30,1050,590),(-400,565,4),700,1800,1200)]"""+s[end:]
s=s.replace("'scope='", "'scope='")
(W/'render_hf06.py').write_text(s)
print('Prepared HF06 preview scripts from validated HF05 renderer.')
