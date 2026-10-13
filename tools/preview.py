"""Offline geometry preview; requires matplotlib and numpy, not used by Dynamo."""
import sys
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/wavehall-matplotlib')
os.environ.setdefault('XDG_CACHE_HOME', '/tmp/wavehall-cache')
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from wave_geometry import build_model
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

meshes=build_model()
colors={'Porcelain':'#e3e2dc','Glass':'#91a9b1','Aluminium':'#606d72',
        'Joint':'#96958e','Concrete':'#b9b6ac'}
fig=plt.figure(figsize=(15,10),facecolor='#eeece7')
ax=fig.add_subplot(111,projection='3d',computed_zorder=False)
ax.set_facecolor('#eeece7')
all_triangles=[]
all_colors=[]
for m in meshes:
    vertices=np.array(m['vertices'])
    triangles=vertices[np.array(m['faces'])]
    norm=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-12)
    light=np.array([-0.4,-0.5,0.8]); light/=np.linalg.norm(light)
    intensity=0.70+0.30*np.abs(norm@light)
    base=np.array(matplotlib.colors.to_rgb(colors[m['material']]))
    facecolors=np.clip(intensity[:,None]*base,0,1)
    all_triangles.extend(triangles)
    all_colors.extend(facecolors)
collection=Poly3DCollection(all_triangles,facecolors=all_colors,edgecolors='none',
                           linewidths=0,rasterized=True,zsort='average')
ax.add_collection3d(collection)
ax.set(xlim=(-70,70),ylim=(-42,42),zlim=(0,46))
ax.set_box_aspect((140,84,46))
ax.view_init(elev=31,azim=-64)
ax.set_axis_off()
ax.set_proj_type('ortho')
ax.set_box_aspect((140,84,46), zoom=1.35)
fig.suptitle('WAVE HALL  /  REVIT 2026',x=0.10,y=0.95,ha='left',fontsize=22,color='#303c41')
fig.text(0.10,0.89,'130 m length   ×   75 m width   ×   40 m height',fontsize=14,color='#52626a')
fig.text(0.10,0.07,'Concept geometry preview • interpreted from reference photos',fontsize=11,color='#52626a')
fig.text(0.10,0.04,'Generic Model components • not a Revit runtime validation or engineered design',fontsize=10,color='#52626a')
fig.subplots_adjust(left=0,right=1,bottom=0.08,top=0.9)
path=Path(__file__).resolve().parents[1]/'output'/'Wave_Hall_Preview.png'
fig.savefig(path,dpi=140,facecolor=fig.get_facecolor())
print(path)
