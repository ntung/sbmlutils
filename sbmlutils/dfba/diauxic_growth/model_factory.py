# -*- coding=utf-8 -*-
"""
This module creates the sub-models and combined comp model for the diauxic model.

Submodels are
- a FBA submodel
- deterministic ODE models

Questions:
- how are the metabolite concentrations kept >= 0 ?
    It seems that the relative change in flux bounds, relative
    to the hard bounds on the exchanges avoids negative concentrations

-----------------------------------------------
Along with the system of dynamic equations, several
additional constraints must be imposed for a realistic prediction
of the metabolite concentrations and the metabolic
fluxes. These include non-negative metabolite and flux levels,
limits on the rate of change of fluxes, and any additional
nonlinear constraints on the transport fluxes.
-----------------------------------------------
vO2:  -> O2
vGlcxt:  -> Glcxt
Ac_out = Ac  # rule

v1: 39.43 Ac + 35 O2 -> X
v2: 9.46 Glcxt + 12.92 O2 -> X
v3: 9.84 Glcxt + 12.73 O2 -> 1.24 Ac + X
v4: 19.23 Glcxt -> 12.12 Ac + X

objective: max(biomass) = max (w1*v1 + w2*v2 + w3*v3 + w4*v4) = max(µ),
            w1 = w2 = w3 = w4 [gdw/mmol]

boundaries:
    # rate of change boundaries => set new lower and upper bound based on
    # the maximal allowed change in boundary over time
    # |d/dt v| <= d/dt v_max
    d/dt v_max(v1) = 0.1 [mmol/h/gdw]
    d/dt v_max(v2) = 0.3 [mmol/h/gdw]
    d/dt v_max(v3) = 0.3 [mmol/h/gdw]
    d/dt v_max(v4) = 0.1 [mmol/h/gdw]

    # in addition the flux bounds must be set, so that not resulting in negative
    # concentrations

    # ? exchange, how does it work ?
    # no external concentrations, but upper bounds for entry in batch reactor
    ub(vO2) = 15 [mmol/h/gdw]
    ub(vGlcxt) = 10 Glcxt/(Km + Glcxt) [mmol/h/gdw]  # Michaelis-Menten kinetics involving glucose concentration

Km = 0.015 mM

-----------------------------------------------

Glcxt:  glucose [mM=mmol/l],    Glcxt(0) = 10.8 [mM]
Ac:     acetate [mM=mmol/l],    Ac(0) = 0.4 [mM]
O2:     oxygen [mM=mmol/l],     O2(0) = 0.21 [mM]
X:      biomass [gdw/l],        X(0) = 0.001 [g/l]

# A*v is row of stoichiometric matrix, i.e. all reactions which change the concentration
d/dt Glcxt = A_Glcxt*v * X                      # [mmol/l/h]
d/dt Ac = A_Ac*v * X                            # [mmol/l/h]
d/dt O2 = A_O2 * v * X + kLa * (O2_gas - O2)    # [mmol/l/h]
d/dt X = (w1*v1 + w2*v2 + w3*v3 + w4*v4)*X      # [g/l/h], due to coefficients conversions to g

O2_gas = 0.21 [mM]  # oxygen in gas phase, constant
kLa = 7.5 [per_h]  # mass transfer coefficient for oxygen

z: vector of metabolite concentrations
v: fluxes per gdw (gram dry weight)
mu: growth rate

-----------------------------------------------
tend = 10 [h]
steps = 10000

-----------------------------------------------

"""
from libsbml import *

import sbmlutils.sbmlio as sbml_io
import sbmlutils.annotation as sbml_annotation
import sbmlutils.comp as comp
from sbmlutils import factory as mc
from sbmlutils.report import sbmlreport


XMLOutputStream.setWriteTimestamp(False)

########################################################################
# General model information
########################################################################
version = 1
notes = XMLNode.convertStringToXMLNode("""
    <body xmlns='http://www.w3.org/1999/xhtml'>
    <h1>Diauxic Growth Model</h1>
    <h2>Description</h2>
    <p>Dynamic Flux Balance Analysis of Diauxic Growth in Escherichia coli</p>

    <p>The key variables in the mathematical model of the metabolic
network are the glucose concentration (Glcxt), the acetate concentration (Ac),
the biomass concentration (X), and the oxygen concentration (O2) in the gas phase.</p>

    <div class="dc:publisher">This file has been produced by
      <a href="https://livermetabolism.com/contact.html" title="Matthias Koenig" target="_blank">Matthias Koenig</a>.
      </div>

    <h2>Terms of use</h2>
      <div class="dc:rightsHolder">Copyright © 2016 Matthias Koenig</div>
      <div class="dc:license">
      <p>Redistribution and use of any part of this model, with or without modification, are permitted provided that
      the following conditions are met:
        <ol>
          <li>Redistributions of this SBML file must retain the above copyright notice, this list of conditions
              and the following disclaimer.</li>
          <li>Redistributions in a different form must reproduce the above copyright notice, this list of
              conditions and the following disclaimer in the documentation and/or other materials provided
          with the distribution.</li>
        </ol>
        This model is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even
             the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.</p>
      </div>
    </body>
""")
creators = [
    mc.Creator(familyName='Koenig', givenName='Matthias', email='konigmatt@googlemail.com',
               organization='Humboldt University Berlin', site='http://livermetabolism.com')
]
main_units = {
    'time': 'h',
    'extent': 'mmol',
    'substance': 'mmol',
    'length': 'm',
    'area': 'm2',
    'volume': 'l',
}
units = [
    mc.Unit('h', [(UNIT_KIND_SECOND, 1.0, 0, 3600)]),

    mc.Unit('g', [(UNIT_KIND_GRAM, 1.0)]),
    mc.Unit('m', [(UNIT_KIND_METRE, 1.0)]),
    mc.Unit('m2', [(UNIT_KIND_METRE, 2.0)]),
    mc.Unit('l', [(UNIT_KIND_LITRE, 1.0)]),

    mc.Unit('per_h', [(UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('mM', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                   (UNIT_KIND_LITRE, -1.0)]),
    mc.Unit('g_per_l', [(UNIT_KIND_GRAM, 1.0),
                        (UNIT_KIND_LITRE, -1.0)]),

    mc.Unit('mmol', [(UNIT_KIND_MOLE, 1.0, -3, 1.0)]),
    mc.Unit('mmol_per_hg', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                            (UNIT_KIND_SECOND, -1.0, 0, 3600), (UNIT_KIND_GRAM, -1.0)]),
    mc.Unit('mmol_per_lh', [(UNIT_KIND_MOLE, 1.0, -3, 1.0),
                            (UNIT_KIND_LITRE, -1.0), (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
    mc.Unit('g_per_lh', [(UNIT_KIND_GRAM, 1.0),
                         (UNIT_KIND_LITRE, -1.0), (UNIT_KIND_SECOND, -1.0, 0, 3600)]),
]

UNIT_AMOUNT = 'mmol'
UNIT_AREA = 'm2'
UNIT_VOLUME ='l'
UNIT_CONCENTRATION = 'mM'
UNIT_FLUX = 'mmol_per_hg'


def add_generic_info(model):
    """ Adds the shared information to the models.

    :param model: SBMLModel instance
    :return:
    """
    sbml_annotation.set_model_history(model, creators)
    mc.create_objects(model, units)
    mc.set_main_units(model, main_units)
    model.setNotes(notes)


####################################################
# FBA submodel
####################################################
def create_fba(sbml_file, directory):
    """
    Create the fba model.
    FBA submodel in FBC v2 which uses parameters as flux bounds.
    """
    sbmlns = SBMLNamespaces(3, 1)
    sbmlns.addPackageNamespace("fbc", 2)
    sbmlns.addPackageNamespace("comp", 1)

    doc_fba = SBMLDocument(sbmlns)
    doc_fba.setPackageRequired("comp", True)
    mdoc = doc_fba.getPlugin("comp")
    doc_fba.setPackageRequired("fbc", False)
    model = doc_fba.createModel()
    mplugin = model.getPlugin("fbc")
    mplugin.setStrict(False)

    # model
    model.setId('diauxic_fba')
    model.setName('FBA submodel (diauxic_fba)')
    model.setSBOTerm(comp.SBO_FLUX_BALANCE_FRAMEWORK)
    add_generic_info(model)

    # Compartments
    compartments = [
        mc.Compartment(sid='bioreactor', value=1.0, unit=UNIT_VOLUME, constant=True, name='bioreactor', spatialDimension=3),
    ]
    mc.create_objects(model, compartments)

    # Species
    # TODO: annotation of boundary fluxes
    species = [
        # internal
        mc.Species(sid='Glcxt', name="glucose", value=10.8, unit='mM', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='Ac', name="acetate", value=0.4, unit='mM', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),

        mc.Species(sid='O2', name="oxygen", value=0.21, unit='mM', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
        mc.Species(sid='X', name="biomass", value=0.001, unit='g_per_l', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),
    ]
    mc.create_objects(model, species)

    parameters = [
        # bounds
        mc.Parameter(sid="lb_irrev", name="lower bound", value=0.0, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="lb", name="lower bound", value=-1000.0, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="ub", name="upper bound", value=1000.0, unit=UNIT_FLUX, constant=True),

        mc.Parameter(sid="ub_vO2", name="ub vO2", value=15.0, unit=UNIT_FLUX, constant=True),
        mc.Parameter(sid="ub_vGlcxt", name="ub vGlcxt", value=10.0, unit=UNIT_FLUX, constant=False),
    ]
    mc.create_objects(model, parameters)

    # reactions with constant flux

    r_vO2 = mc.create_reaction(model, rid="vO2", name="O2 import (vO2)", fast=False, reversible=False,
                            reactants={}, products={"O2": 1}, compartment='bioreactor')
    r_vGlcxt = mc.create_reaction(model, rid="vGlcxt", name="Glcxt import (vGlcxt)", fast=False, reversible=False,
                            reactants={}, products={"Glcxt": 1}, compartment='bioreactor')
    r_vAc = mc.create_reaction(model, rid="vAc", name="Ac import (vAc)", fast=False, reversible=True,
                            reactants={}, products={"Ac": 1}, compartment='bioreactor')
    r_vX = mc.create_reaction(model, rid="vX", name="biomass generation (vX)", fast=False, reversible=False,
                            reactants={"X": 1}, products={}, compartment='bioreactor')

    r_v1 = mc.create_reaction(model, rid="v1", name="v1", fast=False, reversible=False,
                               reactants={"Ac": 39.43, "O2": 35}, products={"X": 1}, compartment='bioreactor')
    r_v2 = mc.create_reaction(model, rid="v2", name="v2", fast=False, reversible=False,
                              reactants={"Glcxt": 9.46, "O2": 12.92}, products={"X": 1}, compartment='bioreactor')
    r_v3 = mc.create_reaction(model, rid="v3", name="v3", fast=False, reversible=False,
                              reactants={"Glcxt": 9.84, "O2": 12.73}, products={"Ac": 1.24, "X": 1}, compartment='bioreactor')
    r_v4 = mc.create_reaction(model, rid="v4", name="v4", fast=False, reversible=False,
                              reactants={"Glcxt": 19.23}, products={"Ac": 12.12, "X": 1}, compartment='bioreactor')


    # flux bounds
    mc.set_flux_bounds(r_vO2, lb="lb_irrev", ub="ub_vO2")
    mc.set_flux_bounds(r_vGlcxt, lb="lb_irrev", ub="ub_vGlcxt")
    mc.set_flux_bounds(r_vAc, lb="lb", ub="ub")

    mc.set_flux_bounds(r_vX, lb="lb_irrev", ub="ub")
    mc.set_flux_bounds(r_v1, lb="lb_irrev", ub="ub")
    mc.set_flux_bounds(r_v2, lb="lb_irrev", ub="ub")
    mc.set_flux_bounds(r_v3, lb="lb_irrev", ub="ub")
    mc.set_flux_bounds(r_v4, lb="lb_irrev", ub="ub")


    # objective function
    mc.create_objective(mplugin, oid="biomass_max", otype="maximize",
                        fluxObjectives={"v1": 1.0, "v2": 1.0, "v3": 1.0, "v4": 1.0})

    # create ports

    comp._create_port(model, pid="bioreactor_port", idRef="bioreactor", portType=comp.PORT_TYPE_PORT)
    # comp._create_port(model, pid="C_port", idRef="C", portType=comp.PORT_TYPE_PORT)
    # comp._create_port(model, pid="R3_port", idRef="R3", portType=comp.PORT_TYPE_PORT)
    # comp._create_port(model, pid="ub_R1_port", idRef="ub_R1", portType=comp.PORT_TYPE_PORT)

    # write SBML file
    sbml_io.write_and_check(doc_fba, os.path.join(directory, sbml_file))

    sbmlreport.create_sbml_report(os.path.join(directory, sbml_file), directory)


####################################################
# ODE flux bounds
####################################################
def create_bounds(sbml_file, directory):
    """"
    Submodel for dynamically calculating the flux bounds.
    The dynamically changing flux bounds are the input to the
    FBA model.
    """
    sbmlns = SBMLNamespaces(3, 1, 'comp', 1)
    doc = SBMLDocument(sbmlns)
    doc.setPackageRequired("comp", True)
    model = doc.createModel()
    model.setId("diauxic_bounds")
    model.setName("ODE bounds submodel")
    model.setSBOTerm(comp.SBO_CONTINOUS_FRAMEWORK)
    add_generic_info(model)

    objects = [
        mc.Compartment(sid='bioreactor', value=1.0, unit=UNIT_VOLUME, constant=True, name='bioreactor',
                       spatialDimension=3),
        mc.Species(sid='Glcxt', name="glucose", value=10.8, unit='mM', hasOnlySubstanceUnits=False,
                   compartment="bioreactor"),

        mc.Parameter(sid='ub_vGlcxt', value=15, unit=UNIT_FLUX, name='ub_vGlcxt', constant=False),
        mc.Parameter(sid='Vmax_vGlcxt', value=15, unit=UNIT_FLUX, name="Vmax_vGlcxt", constant=True),
        mc.Parameter(sid='Km_vGlcxt', value=0.015, unit="mM", name="Km_vGlcxt", constant=True),

        mc.AssignmentRule(sid="ub_vGlcxt", value="Vmax_vGlcxt* Glcxt/(Km_vGlcxt + Glcxt)"),
        # # driving function to test the bound update
        # mc.AssignmentRule(sid="Glcxt", value="5.0 mM + 5.0 mM * sin(time/1 h)")
    ]
    mc.create_objects(model, objects)

    # ports
    comp._create_port(model, pid="bioreactor_port", idRef="bioreactor", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="Glcxt_port", idRef="Glcxt", portType=comp.PORT_TYPE_PORT)
    comp._create_port(model, pid="ub_vGlcxt_port", idRef="ub_vGlcxt", portType=comp.PORT_TYPE_PORT)

    sbml_io.write_and_check(doc, os.path.join(directory, sbml_file))
    sbmlreport.create_sbml_report(os.path.join(directory, sbml_file), directory)

########################################################################################################################
if __name__ == "__main__":
    from dgsettings import fba_file, bounds_file, out_dir
    import os

    # write & check sbml

    create_fba(fba_file, out_dir)
    create_bounds(bounds_file, out_dir)

    # create_ode_update(ode_update_file, out_dir)
    # create_ode_model(ode_model_file, out_dir)