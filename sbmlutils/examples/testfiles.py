"""
Definition of data and files for the tests.
"""

import os
test_dir = os.path.dirname(os.path.abspath(__file__))

################################################################
# Models
################################################################

# demo -----------------------
demo_id = 'Koenig_demo_10'
demo_sbml = os.path.join(test_dir, 'models/demo', '{}.xml'.format(demo_id))
demo_sbml_no_annotations = os.path.join(test_dir, 'models/demo', '{}_no_annotations.xml'.format(demo_id))
demo_annotations = os.path.join(test_dir, 'models/demo', 'demo_annotations.xlsx.csv')

# galactose ------------------
galactose_id = 'galactose_30'
galactose_singlecell_sbml = os.path.join(test_dir, 'models/galactose', '{}.xml'.format(galactose_id))
galactose_singlecell_sbml_no_annotations = os.path.join(test_dir, 'models/galactose', '{}_no_annotations.xml'.format(galactose_id))
galactose_tissue_sbml = os.path.join(test_dir, 'models/galactose', 'Galactose_v128_Nc20_dilution.xml')
galactose_annotations = os.path.join(test_dir, 'models/galactose', 'galactose_annotations.xlsx.csv')

# galactose ------------------
glucose_id = 'Hepatic_glucose_1'
glucose_sbml = os.path.join(test_dir, 'models/glucose', '{}.xml'.format(glucose_id))


# test -----------------------
test_id = 'test_6'
test_sbml = os.path.join(test_dir, 'models/test', '{}.xml'.format(test_id))

# van_der_pol ---------------
vdp_id = "van_der_pol"
vdp_sbml = os.path.join(test_dir, 'models/van_der_pol', '{}.xml'.format(vdp_id))


################################################################
# Data
################################################################
csv_filepath = os.path.join(test_dir, 'data', 'test.csv')

