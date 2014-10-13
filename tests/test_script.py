import numpy as np
import scipy as sp
import OpenPNM
import pytest

def test_cubic_standard_call():
  pn = OpenPNM.Network.Cubic(shape=[3,4,5])
  np.testing.assert_almost_equal(pn['pore.coords'][0], [0.5,0.5,0.5])

def test_trim_extend():
  pn = OpenPNM.Network.Cubic(shape=[5,5,5])
  assert sp.all(sp.in1d(pn.find_neighbor_pores(pores=0),[ 1,  5, 25]))
  assert [pn.Np,pn.Nt] == [125,300]
  pn.trim(pores=[0])
  assert sp.all(sp.in1d(pn.find_neighbor_pores(pores=0),[ 1,  5, 25]))
  assert [pn.Np,pn.Nt] == [124,297]
  pn.extend(pore_coords=[0,0,0],throat_conns=[[124,0]])
  assert [pn.Np,pn.Nt] == [125,298]
  assert sp.all(sp.in1d(pn.find_neighbor_pores(pores=0),[ 1,  5, 25, 124]))

def test_linear_solvers():
  pn = OpenPNM.Network.Cubic([1,40,30], spacing=0.0001)
  geom = OpenPNM.Geometry.Toray090(network=pn,pores=pn.pores(),throats=pn.throats())
  air = OpenPNM.Phases.Air(network=pn,name='air')
  phys_air = OpenPNM.Physics.Standard(network=pn,phase=air,pores=pn.pores(),throats=pn.throats())

  BC1_pores = pn.pores(labels=['left'])
  BC2_pores = pn.pores(labels=['right'])

  alg_1 = OpenPNM.Algorithms.FickianDiffusion(loglevel=20, network=pn,phase=air)
  alg_1.set_boundary_conditions(bctype='Dirichlet', bcvalue=1, pores=BC1_pores)
  alg_1.set_boundary_conditions(bctype='Dirichlet', bcvalue=0, pores=BC2_pores)
  alg_1.run()

  alg_2 = OpenPNM.Algorithms.FickianDiffusion(loglevel=20, network=pn,phase=air)
  alg_2.set_boundary_conditions(bctype='Neumann', bcvalue = -1e-11, pores=BC1_pores)
  alg_2.set_boundary_conditions(bctype='Dirichlet', bcvalue=0, pores=BC2_pores)
  alg_2.run()

  alg_3 = OpenPNM.Algorithms.FickianDiffusion(loglevel=20, network=pn,phase=air)
  alg_3.set_boundary_conditions(bctype='Neumann_group', bcvalue = -3e-10, pores=BC1_pores)
  alg_3.set_boundary_conditions(bctype='Dirichlet', bcvalue=0, pores=BC2_pores)
  alg_3.run()

  print( alg_1['pore.'+air.name+'_mole_fraction'][BC1_pores] )
  print( alg_2['pore.'+air.name+'_mole_fraction'][BC1_pores] )
  print( alg_3['pore.'+air.name+'_mole_fraction'][BC1_pores] )

  assert round(sp.absolute(alg_1.rate(BC1_pores))[0],16) == round(sp.absolute(alg_1.rate(BC2_pores))[0],16)
  assert round(sp.absolute(alg_2.rate(BC2_pores))[0],16) == round(sp.absolute(sp.unique(alg_2['pore.'+air.name+'_bcval_Neumann']))[0]*len(BC1_pores),16)
  assert round(sp.absolute(alg_3.rate(BC2_pores))[0],16) == round(sp.absolute(sp.unique(alg_3['pore.'+air.name+'_bcval_Neumann_group']))[0],16)

def test_add_boundary():
  pn = OpenPNM.Network.Cubic(shape=[5,5,5])
  pn.add_boundaries()

  keys_expected = {'pore.back', 'pore.bottom', 'pore.top_boundary',
  'pore.right_boundary', 'throat.back_boundary', 'throat.all',
  'throat.bottom_boundary', 'throat.front_boundary', 'pore.boundary',
  'throat.left_boundary', 'throat.conns', 'throat.top_boundary',
  'pore.back_boundary', 'pore.top', 'pore.front_boundary', 'pore.all',
  'pore.front', 'pore.left_boundary', 'throat.boundary', 'pore.bottom_boundary',
  'throat.right_boundary', 'pore.coords', 'pore.internal', 'pore.index',
  'pore.left', 'pore.right'}

  keys_found = set(pn.keys())

  symmetric_diff = keys_found ^ keys_expected
  assert not symmetric_diff

def test_open_air_diffusivity():
    pn = OpenPNM.Network.Cubic([5,5,5], spacing=1, name='net', loglevel=30)
    pn.add_boundaries()
    Ps = pn.pores('boundary',mode='difference')
    Ts = pn.find_neighbor_throats(pores=Ps,mode='intersection',flatten=True)
    geom = OpenPNM.Geometry.Cube_and_Cuboid(network=pn,pores=Ps,throats=Ts)
    geom['pore.diameter'] = 0.999999
    geom['throat.diameter'] = 0.999999
    geom.regenerate(['pore.diameter','throat.diameter'],mode='exclude')
    Ps = pn.pores('boundary')
    Ts = pn.find_neighbor_throats(pores=Ps,mode='not_intersection')
    boun = OpenPNM.Geometry.Boundary(network=pn,pores=Ps,throats=Ts,shape='cubes')
    air = OpenPNM.Phases.Air(network=pn,name='air')
    Ps = pn.pores()
    Ts = pn.throats()
    phys_air = OpenPNM.Physics.Standard(network=pn,phase=air,pores=Ps,throats=Ts,name='phys_air')
    BC1_pores = pn.pores(labels=['top_boundary'])
    BC2_pores = pn.pores(labels=['bottom_boundary'])
    print('length =',round(pn.domain_length(BC1_pores,BC2_pores)))
    print('area = ',round(pn.domain_area(BC1_pores),2),round(pn.domain_area(BC2_pores),2))
    Diff = OpenPNM.Algorithms.FickianDiffusion(loglevel=30, network=pn,phase=air)
    # Assign Dirichlet boundary conditions to top and bottom surface pores
    Diff.set_boundary_conditions(bctype='Dirichlet', bcvalue=0.6, pores=BC1_pores)
    Diff.set_boundary_conditions(bctype='Dirichlet', bcvalue=0.4, pores=BC2_pores)
    Diff.run()
    Diff.update_results()
    Diff_deff = Diff.calc_eff_diffusivity()/np.mean(air['pore.diffusivity'])
    assert np.round(Diff_deff,3) == 1

def test_thermal_conduction():
    #Generate Network and clean up boundaries (delete z-face pores)
    divs = [10,50]
    Lc   = 0.1  # cm
    pn = OpenPNM.Network.Cubic(name='net', shape= divs, spacing = Lc, loglevel=20)
    pn.add_boundaries()
    pn.trim(pores=pn.pores(['top_boundary','bottom_boundary']))
    #Generate Geometry objects for internal and boundary pores
    Ps = pn.pores('internal')
    Ts = pn.throats()
    geom = OpenPNM.Geometry.GenericGeometry(network=pn,pores=Ps,throats=Ts,name='geom',loglevel=20)
    geom['pore.area']     = Lc**2
    geom['pore.diameter'] = Lc
    geom['throat.length'] = 1e-25
    geom['throat.area']   = Lc**2
    Ps = pn.pores('boundary')
    boun = OpenPNM.Geometry.GenericGeometry(network=pn,pores=Ps,name='boundary',loglevel=20)
    boun['pore.area']     = Lc**2
    boun['pore.diameter'] =  1e-25
    #Create Phase object and associate with a Physics object
    Cu = OpenPNM.Phases.GenericPhase(network=pn,name='copper',loglevel=20)
    Cu['pore.thermal_conductivity'] = 1.0  # W/m.K
    phys = OpenPNM.Physics.GenericPhysics(network=pn,phase=Cu,pores=pn.pores(),throats=pn.throats(),loglevel=10)
    mod = OpenPNM.Physics.models.thermal_conductance.series_resistors
    phys.add_model(propname='throat.thermal_conductance',model=mod)
    phys.regenerate()  # Update the conductance values
    #Setup Algorithm object
    Fourier_alg = OpenPNM.Algorithms.FourierConduction(network=pn,phase=Cu,loglevel=10)
    inlets = pn.pores('back_boundary')
    outlets = pn.pores(['front_boundary','left_boundary','right_boundary'])
    T_in = 30*sp.sin(sp.pi*pn['pore.coords'][inlets,1]/5)+50
    Fourier_alg.set_boundary_conditions(bctype='Dirichlet',bcvalue=T_in,pores=inlets)
    Fourier_alg.set_boundary_conditions(bctype='Dirichlet',bcvalue=50,pores=outlets)
    Fourier_alg.run()
    Fourier_alg.update_results()
    #Calculate analytical solution over the same domain spacing
    Cu['pore.analytical_temp'] = 30*sp.sinh(sp.pi*pn['pore.coords'][:,0]/5)/sp.sinh(sp.pi/5)*sp.sin(sp.pi*pn['pore.coords'][:,1]/5) + 50
    b = Cu['pore.analytical_temp'][pn.pores('geom')]
    a = Cu['pore.temperature'][pn.pores('geom')]
    a = sp.reshape(a,(divs[0],divs[1]))
    b = sp.reshape(b,(divs[0],divs[1]))
    diff = a - b
    assert sp.amax(np.absolute(diff)) < 0.015

def test_Darcy_alg():
    #Generate Network and clean up some of boundaries
    divs = [1,50,10]
    Lc = 0.00004
    pn = OpenPNM.Network.Cubic(name='net',shape = divs, spacing = Lc,loglevel=20)
    pn.add_boundaries()
    Ps = pn.pores(['front_boundary','back_boundary'])
    pn.trim(pores=Ps)
    #Generate Geometry objects for internal and boundary pores
    Ps = pn.pores('boundary',mode='difference')
    Ts = pn.throats()
    geom = OpenPNM.Geometry.Toray090(network=pn,pores=Ps,throats=Ts,name='GDL')
    Ps = pn.pores('boundary')
    boun = OpenPNM.Geometry.Boundary(network=pn,pores=Ps,name='boundary')
    #Create Phase object and associate with a Physics object
    air = OpenPNM.Phases.Air(network=pn,name='air')
    Ps = pn.pores()
    Ts = pn.throats()
    phys = OpenPNM.Physics.GenericPhysics(network=pn,phase=air,pores=Ps,throats=Ts)
    from OpenPNM.Physics import models as pm
    phys.add_model(propname='throat.hydraulic_conductance',
                   model=pm.hydraulic_conductance.hagen_poiseuille)
    phys.regenerate()  # Update the conductance values
    #Setup Algorithm objects
    Darcy1 = OpenPNM.Algorithms.StokesFlow(network=pn,phase=air,name='Darcy1')
    inlets = pn.pores('bottom_boundary')
    Ps = pn.pores('top_boundary')
    outlets = Ps[pn['pore.coords'][Ps,1]<(divs[1]*Lc/2)]
    P_out = 0  # Pa
    Q_in = 0.6667*(Lc**2)*divs[1]*divs[0]  # m^3/s
    Darcy1.set_boundary_conditions(bctype='Neumann_group',bcvalue=-Q_in,pores=inlets)
    Darcy1.set_boundary_conditions(bctype='Dirichlet',bcvalue=P_out,pores=outlets)
    Darcy1.run()
    Darcy1.update_results()
    print('pore pressure for Darcy1 algorithm:')
    print(air['pore.pressure'])
    Darcy2 = OpenPNM.Algorithms.StokesFlow(network=pn,phase=air,name='Darcy2')
    inlets = pn.pores('bottom_boundary')
    outlets = pn.pores('top_boundary')
    P_out = 10  # Pa
    P_in = 1000  # Pa
    Darcy2.set_boundary_conditions(bctype='Dirichlet',bcvalue=P_in,pores=inlets)
    Darcy2.set_boundary_conditions(bctype='Dirichlet',bcvalue=P_out,pores=outlets)
    Darcy2.run()
    print('pore pressure for Darcy2 algorithm:')
    print(Darcy2['pore.air_pressure'])
    Q = -Darcy2.rate(inlets)
    K = Q*air['pore.viscosity'][0]*divs[2]*Lc/(divs[0]*divs[1]*Lc**2*(P_in-P_out))
    Vp = sp.sum(pn['pore.volume']) + sp.sum(pn['throat.volume'])
    Vb = sp.prod(divs)*Lc**3
    e = Vp/Vb
    print('Effective permeability: ',K,'- Porosity: ',e)

    assert round(sp.absolute(Darcy1.rate(outlets))[0],16) == round(sp.absolute(sp.unique(Darcy1['pore.'+air.name+'_bcval_Neumann_group']))[0],16)
    assert round(sp.absolute(Darcy2.rate(inlets))[0],16) == round(sp.absolute(Darcy2.rate(outlets))[0],16)

def test_mapping():
    # Create small cubic network
    pn = OpenPNM.Network.Cubic(shape=[3,3,3],spacing=0.0001,name='net',loglevel=20)
    # Assign 3 different geometries to each layer in the z-direction
    Pa = sp.arange(0,9)
    geom1 = OpenPNM.Geometry.GenericGeometry(network=pn,pores=Pa,throats=pn.Ts)
    Pb = sp.arange(9,18)
    geom2 = OpenPNM.Geometry.GenericGeometry(network=pn,pores=Pb)
    Pc = sp.arange(18,27)
    geom3 = OpenPNM.Geometry.GenericGeometry(network=pn,pores=Pc)
    # Create an index in the Network
    pn['pore.num1'] = pn.Ps
    # Create the same index across each geom
    geom1['pore.num2'] = Pa
    geom2['pore.num2'] = Pb
    geom3['pore.num2'] = Pc
    # Confirm two indexes match
    sp.all(pn['pore.num1'] == pn['pore.num2'])
    # Trim column from center of Network
    pn.trim(pores=[4,13,22])
    # Confirm index still match
    sp.all(pn['pore.num1'] == pn['pore.num2'])
    # Check that mapping works
    a = pn.pop('pore.map',None)
    sp.all(pn['pore.map'] == pn.Ps)
    # Check mapping between each Geometry object and in both directions
    a = geom1.map_pores(geom1.Ps,pn)
    b = pn.map_pores(a,geom1)
    assert(sp.all(b == ([0, 1, 2, 3, 4, 5, 6, 7])))
    a = geom2.map_pores(geom2.Ps,pn)
    b = pn.map_pores(a,geom2)
    assert(sp.all(b == ([0, 1, 2, 3, 4, 5, 6, 7])))
    a = geom3.map_pores(geom3.Ps,pn)
    b = pn.map_pores(a,geom3)
    assert(sp.all(b == ([0, 1, 2, 3, 4, 5, 6, 7])))

if __name__ == '__main__':
  pytest.main()
