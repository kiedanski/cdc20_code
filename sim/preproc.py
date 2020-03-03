import dill
import numpy as np
import scipy as sp
import pandas as pd

import os
import sys
from pathlib import Path

from sim.constants import OUTDIR

outdir = Path.home() / OUTDIR

game_files = outdir.glob('*_game.pkl')
#games = {}
for gf in game_files:
    new_f = str(gf) + '.proc'
    if not os.path.isfile(new_f):
        with open(gf, 'rb') as fh: data = dill.load(fh)
        id_ = os.path.basename(gf).split('_')[0]
        #games[id_] = data
        gm = data
        partial = (gm.__str__(),gm.N, gm.T, gm.time_solve_fast, gm.time_get_valfunc, )
        with open(str(gf) + '.proc', 'w') as f2: f2.write(str(partial))
    

dist_files = outdir.glob('*_dist.pkl')
#dists = {}
for gf in dist_files:
    new_f = str(gf) + '.proc'
    if not os.path.isfile(new_f):
        with open(gf, 'rb') as fh: data = dill.load(fh)
        id_ = os.path.basename(gf).split('_')[0]
        #dists[id_] = data
        dis = data
        partial = (np.sum(dis[1]), dis[2])
        
        with open(str(gf) + '.proc', 'w') as f2: f2.write(str(partial))


#data = []
#for k in games:
#   gm = games[k] 
#   dis = dists[k]
#   
#   time_d = np.sum(dis[1])
#   partial = (gm.__str__(),gm.N, gm.T, gm.time_solve_fast, gm.time_get_valfunc, )
#   partial = partial + (time_d, dis[2])
#   data.append(partial)
#
#df = pd.DataFrame(data)
#df.columns = ['game', 'N', 'T', 'centralized', 'valfunc', 'distributed', 'iterations']
#df = df.sort_values(['N', 'iterations'])