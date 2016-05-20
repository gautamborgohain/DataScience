import os
from flask import Flask, Response, request, abort,send_file
import eve
import pandas as pd
import numpy as np
import pylab as pl
import time
import base64

from io import StringIO

# In[3]:
# from settings import BASE_DIR

app = eve.Eve()
BASE_DIR = '/Users/gautamborgohain/DEweb/REST_API_EVE_Part-1'
df = pd.read_excel('/Users/gautamborgohain/Google Drive/Data Extraction /actors_scores.xlsx')


###
class Radar(object):
    def __init__(self, fig, titles, labels, rect=None):
        if rect is None:
            rect = [0.05, 0.05, 0.95, 0.95]

        self.n = len(titles)
        self.angles = np.arange(0, 0 + 360, 360.0 / self.n)
        self.axes = [fig.add_axes(rect, projection="polar", label="axes%d" % i)
                     for i in range(self.n)]

        self.ax = self.axes[0]
        self.ax.set_thetagrids(self.angles, labels=titles, fontsize=14)

        for ax in self.axes[1:]:
            ax.patch.set_visible(False)
            ax.grid("off")
            ax.xaxis.set_visible(False)

        for ax, angle, label in zip(self.axes, self.angles, labels):
            ax.set_rgrids(range(1, 7), angle=angle, labels=label)
            ax.spines["polar"].set_visible(False)
            ax.set_ylim(0, 6)
            self.fig = fig

    def plot(self, values, *args, **kw):
        angle = np.deg2rad(np.r_[self.angles, self.angles[0]])
        values = np.r_[values, values[0]]
        self.ax.plot(angle, values, *args, **kw)
        print("before saving")
        self.fig.savefig('plot.png')

    ###


####
def compareActors(act1, act2):
    #     plt.style.use('seaborn-darkgrid')

    titles = ['Overall Nomination Rate', 'Overall Strike Rate', 'Overall Win Rate', 'Big 5 nommination rate',
              'Big 5 strike rate', 'Big 5 Win rate']
    labels = [
        list("12345"), list("12345"), list("12345"),
        list("12345"), list("12345"), list("12345")
    ]
    fig = pl.figure(figsize=(8, 8))

    # Search dataframe for the actor

    A = df[df['name'] == act1][
        ['name', 'Nom_rate', 'strike_rate', 'Win_rate', 'Big_5_nom_rate', 'Big_5_strike_rate', 'Big_5_Win_rate']]
    A = np.array(A).ravel()
    Act1 = A[0]  # Actor name
    A = A[1:len(A)]

    B = df[df['name'] == act2][
        ['name', 'Nom_rate', 'strike_rate', 'Win_rate', 'Big_5_nom_rate', 'Big_5_strike_rate', 'Big_5_Win_rate']]
    B = np.array(B).ravel()
    Act2 = B[0]  # Actor name
    B = B[1:len(B)]

    combined = A + B
    Max = 5
    Min = 1
    actualMax = np.max(combined)
    actualMin = np.min(combined)

    percentA = (A - actualMin) / (actualMax - actualMin);
    outputA = percentA * (Max - Min) + Min;

    percentB = (B - actualMin) / (actualMax - actualMin);
    outputB = percentB * (Max - Min) + Min;
    print("before calling Radar")
    radar = Radar(fig, titles, labels)
    radar.plot(outputA, "-", lw=2, color="b", alpha=0.4, label=Act1)
    radar.plot(outputB, "-", lw=2, color="r", alpha=0.4, label=Act2)
    radar.ax.legend(loc=(-0.3, 0.1))


####


@app.route('/images')
def serve_images():
    print("atleast here")
    try:
        compareActors('Leonardo DiCaprio', 'Tom Hardy')

    except Exception as e:
        print(e)

    print("done here")

    try:
        with open('/Users/gautamborgohain/DEweb/REST_API_EVE_Part-1/plot.png', 'rb') as inf:
            im = inf.read()
        io = StringIO.StringIO()
        im.save(io, format='JPEG')
        return Response(io.getvalue(), mimetype='image/jpeg')
    except IOError:
        print("err")
        abort(404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
