"""Reuse the established actual-OBJ material renderer for fixture placement QA."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT.parent/'KIAH_R25_Realism_R22/source/render_r25.py').read_text()
text=text.replace("spec_from_file_location('r25',ROOT/'source/build_r25.py')","spec_from_file_location('r26',ROOT/'source/build_r26.py')")
text=text.replace('g=b.g;PACK=b.PACK;scene=[]','r26=b;b=b.b;g=r26.g;PACK=r26.PACK;scene=[]')
text=text.replace('qa/R25_Roundtrip.txt','qa/R26_Roundtrip.txt')
text=text.replace("not Path(q['resource']).stem.startswith('r25_')","not Path(q['resource']).stem.startswith(('r25_','r26_'))")
text=text[:text.index("render('Headquarters_Arrival.png'")]+'''render('R26_Terminal_Fixtures.png','R26 | Actual exported terminal work-light fixtures',[2817,467,22],[2791,420,5.0],47)
render('R26_Hangar_Fixtures.png','R26 | Actual exported hangar-mounted work lights',[2590,390,38],[2508,413,14],86)
(OUT/'Render_Evidence.json').write_text(json.dumps(dict(renders=2,triangles=len(scene),actual_export_meshes=True,runtime_tested=False,notes=['Actual geometry and texture preview only; this renderer does not simulate X-Plane light spill or animated jetway arms.']),indent=2))
print(json.dumps(dict(renders=2,triangles=len(scene))))
'''
exec(compile(text,str(__file__),'exec'))
