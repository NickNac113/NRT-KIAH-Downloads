"""Actual exported object previews; not simulator weather or traffic evidence."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT.parent/'KIAH_R25_Realism_R22/source/render_r25.py').read_text()
text=text.replace("spec_from_file_location('r25',ROOT/'source/build_r25.py')","spec_from_file_location('r27',ROOT/'source/build_r27.py')")
text=text.replace('g=b.g;PACK=b.PACK;scene=[]','r27=b;b=b.r25;g=r27.g;PACK=r27.PACK;scene=[]')
text=text.replace('qa/R25_Roundtrip.txt','qa/R27_Roundtrip.txt')
text=text.replace("not Path(q['resource']).stem.startswith('r25_')","not Path(q['resource']).stem.startswith(('r25_','r26_','r27_'))")
text=text.replace("    elif q['resource'] in b.LIBMAP", "    elif q['resource']==r27.MAST_RESOURCE:\n        p=Path('X:/X-Plane 12/Resources/default scenery/airport scenery/Common_Elements/Lighting/flood_1_led_24m_omni.obj')\n    elif q['resource'] in b.LIBMAP")
text=text[:text.index("render('Headquarters_Arrival.png'")]+'''render('R27_Corner_Jetways.png','R27 | Corner mast and translated NRT9 terminal connections',[2772,492,43],[2758,422,5.0],117)
render('R27_Canopy_Floor.png','R27 | Modeled canopy floor with preserved guidance',[2574,380,36],[2648,320,4],102)
render('R27_Indoor_Floor.png','R27 | Indoor Parking receives the MH floor treatment',[2600,399,49],[2475,359,4],170)
(OUT/'Render_Evidence.json').write_text(json.dumps(dict(renders=3,triangles=len(scene),actual_export_meshes=True,runtime_tested=False,notes=['Actual exported object geometry and textures. Native animated jetway arms are not rendered.','The preview does not simulate X-Plane rain, dynamic lighting, vehicle movement, or docking.']),indent=2))
print(json.dumps(dict(renders=3,triangles=len(scene))))
'''
exec(compile(text,str(__file__),'exec'))
