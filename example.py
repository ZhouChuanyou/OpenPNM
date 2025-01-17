import numpy as np
import openpnm as op
from openpnm.models.physics import source_terms

# %% Initialization: create Workspace and project objects.
ws = op.Workspace()
proj = ws.new_project()
np.random.seed(9)

# %% Create network, geometry, phase, and physics objects
pn = op.network.Cubic(shape=[10, 10, 10], spacing=1e-4, project=proj)
geo = op.geometry.SpheresAndCylinders(network=pn, pores=pn.Ps, throats=pn.Ts)
air = op.phases.Air(network=pn, name='air')
water = op.phases.Water(network=pn, name='h2o')
hg = op.phases.Mercury(network=pn, name='hg')
phys_air = op.physics.Standard(network=pn, phase=air, geometry=geo)
phys_water = op.physics.Standard(network=pn, phase=water, geometry=geo)
phys_hg = op.physics.Standard(network=pn, phase=hg, geometry=geo)

# %% Perform porosimetry simulation
mip = op.algorithms.Porosimetry(network=pn, phase=hg)
mip.set_inlets(pores=pn.pores(['top', 'bottom']))
mip.run()
hg.update(mip.results(Pc=70000))
# mip.plot_intrusion_curve()

# %% Perform Stokes flow simulation
perm = op.algorithms.StokesFlow(network=pn, phase=water)
perm.set_value_BC(pores=pn.pores('right'), values=0)
perm.set_value_BC(pores=pn.pores('left'), values=101325)
perm.run()
water.update(perm.results())
Keff = perm.calc_effective_permeability()[0]
print(f"Effective permeability: {Keff:.2e}")

# %% Perform reaction-diffusion simulation
# Add reaction to phys_air
phys_air['pore.n'] = 2
phys_air['pore.A'] = -1e-5
phys_air.add_model(
    propname='pore.2nd_order_rxn',
    model=source_terms.standard_kinetics,
    X='pore.concentration', prefactor='pore.A', exponent='pore.n',
    regen_mode='deferred'
)
# Set up Fickian diffusion simulation
rxn = op.algorithms.FickianDiffusion(network=pn, phase=air)
rxn.settings['solver'] = 'spsolve'
Ps = pn.find_nearby_pores(pores=50, r=5e-4, flatten=True)
rxn.set_source(propname='pore.2nd_order_rxn', pores=Ps)
rxn.set_value_BC(pores=pn.pores('top'), values=1)
rxn.run()
air.update(rxn.results())

# %% Perform pure diffusion simulation to get effective diffusivity
fd = op.algorithms.FickianDiffusion(network=pn, phase=air)
fd.set_value_BC(pores=pn.pores('left'), values=1)
fd.set_value_BC(pores=pn.pores('right'), values=0)
fd.run()
Deff = fd.calc_effective_diffusivity()[0]
print(f"Effective diffusivity: {Deff:.2e}")

# %% Output network and the phases to a VTP file for visualization in Paraview
proj.export_data(phases=[hg, air, water], filename='output.vtp')
