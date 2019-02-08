"""
Check the charge and formula balance of the model.
Run some simple FBA simulations.
"""
from __future__ import print_function, division

import os

import model
import roadrunner
import pandas as pd
from matplotlib import pylab as plt

import os
import libsbml
from sbmlutils.modelcreator.creator import Factory


models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))

print('-'*80)
print(models_dir)
print('-' * 80)

factory = Factory(modules=['sbmlutils.examples.models.tiny_model.model'],
                  target_dir=os.path.join(models_dir, 'results'),
                  annotations=os.path.join(models_dir, 'annotations.xlsx'))
# factory = Factory(modules=['sbmlutils.examples.models.tiny_model.model2'],
#                  target_dir=os.path.join(models_dir, 'results'))
_, _, tiny_sbml = factory.create(tmp=False)


# SBML file
# tiny_sbml = os.path.join(os.path.dirname(os.path.abspath(__file__)),
#                         'results',
#                         '{}_{}.xml'.format(model.mid, model.version))


r = roadrunner.RoadRunner(tiny_sbml)
r.timeCourseSelections = ["time"] + r.model.getBoundarySpeciesIds() + r.model.getFloatingSpeciesIds() + r.model.getReactionIds() + r.model.getGlobalParameterIds()
r.timeCourseSelections += ["[{}]".format(key) for key in r.model.getFloatingSpeciesIds()]
print(r)
s = r.simulate(0, 700, steps=700)
df = pd.DataFrame(s, columns=s.colnames)
# r.plot()

f, (ax1, ax2) = plt.subplots(nrows=1, ncols=2)
ax1.set_title("SBML species")
ax1.plot(df.time, df['[glc]'])
ax1.plot(df.time, df['[g6p]'])
ax1.plot(df.time, df['[atp]'])
ax1.plot(df.time, df['[adp]'])
ax1.plot(df.time, df['a_sum'], color="grey", linestyle="--", label="[atp]+[adp]")
ax1.set_ylabel("concentration [mmole/litre]=[mM]")

ax2.set_title("SBML reactions")
ax2.plot(df.time, 1E6*df.GK)
ax2.plot(df.time, 1E6*df.ATPASE)
ax2.set_ylabel("reaction rate 1E6[mmole/s]")

for ax in (ax1, ax2):
    ax.legend()
    ax.set_xlabel("time [s]")

plt.show()
f.savefig("tiny_example.png", bbox_inches="tight")


#r = roadrunner.RoadRunner(tiny_sbml)
#r.integrator.setValue("relative_tolerance", 1E-18)
#r.integrator.setValue("absolute_tolerance", 1E-18)
#s = r.simulate(0, 100, steps=100)
#df = pd.DataFrame(s, columns=s.colnames)
#r.plot()



