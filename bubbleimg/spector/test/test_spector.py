
import pytest
import shutil
import os
import astropy.units as u
import numpy as np
import astropy.table as at
import filecmp
import numpy.testing as npt

from ...obsobj import obsObj

from .. import spector

ra = 140.099341430207
dec = 0.580162492432517
z = 0.4114
dir_parent = './testing/'
dir_obj = './testing/SDSSJ0920+0034/'
dir_verif = 'test_verification_data/SDSSJ0920+0034/'
survey = 'hsc'

@pytest.fixture(scope="module", autouse=True)
def setUp_tearDown():
	""" rm ./testing/ and ./test2/ before and after testing"""

	# setup
	if os.path.isdir(dir_parent):
		shutil.rmtree(dir_parent)

	os.makedirs(dir_obj)
	# shutil.copytree(dir_verif, dir_obj)
	shutil.copyfile(dir_verif+'spec.fits', dir_obj+'spec.fits')

	# yield
	# # tear down
	# if os.path.isdir(dir_parent):
	# 	shutil.rmtree(dir_parent)


@pytest.fixture
def obj_dirobj():
	return obsObj(ra=ra, dec=dec, dir_obj = dir_obj)


@pytest.fixture
def spector1(obj_dirobj):
	obj = obj_dirobj
	return spector.Spector(obj=obj, survey_spec='boss', survey='hsc')


def test_spector_init(spector1):
	s = spector1

	spec, ws = s.get_spec_ws()

	assert len(spec) == len(ws)


def test_spector_init_error_survey_spec(obj_dirobj):
	""" complain when the survey_spec is set to a wrong value"""
	obj = obj_dirobj

	with pytest.raises(Exception) as e: 
		s = spector.Spector(obj=obj, survey_spec='sdss')


def test_spector_init_autochoose_survey_spec(obj_dirobj):
	""" complain when the survey_spec is set to a wrong value"""
	obj = obj_dirobj

	s = spector.Spector(obj=obj, survey='hsc')

	assert s.survey_spec == 'boss'


def test_spector_init_getsurvey_fromobj(obj_dirobj):
	""" complain when the survey_spec is set to a wrong value"""
	obj = obj_dirobj
	obj.survey = 'cfht'

	s = spector.Spector(obj=obj)

	assert s.survey == 'cfht'

	s = spector.Spector(obj=obj, survey='hsc')

	assert s.survey == 'hsc'


def test_spector_init_error_no_survey(obj_dirobj):
	""" complain when no survey is speficied either through obj or as attr of spector"""
	obj = obj_dirobj

	with pytest.raises(Exception) as e:
		s = spector.Spector(obj=obj)



def test_spector_make_spec_decomposed_ecsv(spector1):
	s = spector1
	s.make_spec_decomposed_ecsv(overwrite=True)

	assert os.path.isfile(s.dir_obj+'spec_decomposed.ecsv')

	tab = at.Table.read(s.dir_obj+'spec_decomposed.ecsv', format='ascii.ecsv')

	units = [tab[col].unit for col in ['spec', 'speccont', 'specline']]

	# assert all units are identical
	assert len(set(units)) == 1


def test_spector_make_spec_contextrp_ecsv(spector1):
	s = spector1
	fn = s.dir_obj+'spec_contextrp.ecsv'
	s.make_spec_contextrp_ecsv(overwrite=True)

	assert os.path.isfile(fn)

	tab = at.Table.read(fn, format='ascii.ecsv')

	assert tab['ws'].unit == u.AA
	assert tab['contextrp'].unit == u.Unit("1e-17 erg / (Angstrom cm2 s)")


def test_spector_get_contline(spector1):
	s = spector1

	spec, ws = s.get_spec_ws_from_spectab(component='all')
	speccont, __ = s.get_spec_ws_from_spectab(component='cont')
	specline, __ = s.get_spec_ws_from_spectab(component='line')

	assert len(speccont) == len(ws)
	assert len(specline) == len(ws)

	assert max(speccont) <= max(spec)
	assert max(specline) <= max(spec)


def test_spector_plot_spec(spector1):
	s = spector1
	
	s.plot_spec(wfilters=True, wconti=True, wcontextrp=True, wline=True, overwrite=True)
	assert os.path.isfile(s.dir_obj+'spec.pdf')



def test_spector_calc_Fnu_in_band(obj_dirobj):
	obj = obj_dirobj
	s = spector.Spector(obj=obj, survey_spec='boss', survey='sdss')
	s.obj.sdss.load_photoobj()

	for band in s.bands:
		Fnu = s._calc_Fnu_in_band(band=band, component='all')
		mAB = s._calc_mAB_in_band(band=band, component='all')

		convovledflux = Fnu.to(u.nanomaggy).value
		fiber2flux = s.obj.sdss.photoobj['fiber2Flux_'+band] # in nanomaggy
		fiber2mag = s.obj.sdss.photoobj['fiber2Mag_'+band]
		assert np.absolute(convovledflux - fiber2flux) < 10.
		assert np.absolute(mAB.value - fiber2mag) < 1.


def test_spector_make_spec_mag(spector1): 
	s = spector1
	s.make_spec_mag(overwrite=True)

	fn = s.dir_obj+'spec_mag.csv'
	assert os.path.isfile(fn)

	tab = at.Table.read(fn, comment='#', format='ascii.csv')

	for band in s.bands:
		assert 'specMag_{0}'.format(band) in tab.colnames
		assert 'speccontMag_{0}'.format(band) in tab.colnames
		assert 'speclineMag_{0}'.format(band) in tab.colnames
		assert 'speccontextrpMag_{0}'.format(band) in tab.colnames

		assert 'specFnu_{0}'.format(band) in tab.colnames
		assert 'speccontFnu_{0}'.format(band) in tab.colnames
		assert 'speclineFnu_{0}'.format(band) in tab.colnames
		assert 'speccontextrpFnu_{0}'.format(band) in tab.colnames



def test_spector_get_spec_mag(spector1): 
	s = spector1
	tab = s.get_spec_mag_tab()

	for band in s.bands:
		assert 'specMag_{0}'.format(band) in tab.colnames
		assert 'speccontMag_{0}'.format(band) in tab.colnames
		assert 'speclineMag_{0}'.format(band) in tab.colnames

		assert 'specFnu_{0}'.format(band) in tab.colnames
		assert 'speccontFnu_{0}'.format(band) in tab.colnames
		assert 'speclineFnu_{0}'.format(band) in tab.colnames



def test_spector_get_spec_mag_value(spector1):
	s = spector1

	x = s.get_spec_mag_value(component='line', fluxquantity='mag', band='i')
	assert isinstance(x, np.float64)
	npt.assert_almost_equal(x, 21.726328586041113, decimal=1)

	x = s.get_spec_mag_value(component='cont', fluxquantity='fnu', band='g')
	npt.assert_almost_equal(x, 1.6768567248522026, decimal=2)


def test_spector_get_fnu_ratio_band1_over_band2(spector1):
	s = spector1
	b1 = 'i'
	b2 = 'z'
	x = s.get_fnu_ratio_band1_over_band2(band1=b1, band2=b2, component='contextrp')
	
	npt.assert_almost_equal(x, 0.7281524829527901, decimal=2)


def test_spector_get_line_obs_wave(spector1):
	s = spector1

	w = s._get_line_obs_wave(line='OIII5008', wunit=False)
	npt.assert_almost_equal(w, 7068.724090912, decimal=1)

	w = s._get_line_obs_wave(line='OIII5008', wunit=True)
	assert w.unit == u.Unit("AA")


def test_spector_calc_fline_over_fnuband(spector1):
	s = spector1


	ri = s.calc_fline_over_fnuband(band='i', line='OIII5008')
	assert ri.unit == u.Unit('Hz')

	r4 = s.calc_fline_over_fnuband(band='i', line='OIII4960')

	assert ri > r4

	# the line is marginally within the coverage of r so the correction factor should be larger
	rr = s.calc_fline_over_fnuband(band='r', line='OIII5008')
	assert ri < rr

	with pytest.raises(Exception) as e:
		r = s.calc_fline_over_fnuband(band='z', line='OIII5008')

	with pytest.raises(Exception) as e:
		r = s.calc_fline_over_fnuband(band='y', line='OIII5008')


def test_spector_list_lines_in_band(spector1):
	s = spector1

	band = 'i'
	l = s._list_stronglines_in_band(band=band, threshold=0.01)
	assert set(l) == set(['Hb', 'OIII4960', 'OIII5008'])
	
	band = 'z'
	l = s._list_stronglines_in_band(band=band, threshold=0.01)
	assert set(l) == set(['OI6302', 'NII6550', 'Ha', 'NII6585', 'SII6718'])
	
	band = 'r'
	l = s._list_stronglines_in_band(band=band, threshold=0.2)
	assert set(l) == set(['NeIII3870', 'NeIII3969', 'Hg', 'Hb', 'OIII4960']) # , 'OIII4364' was exluded
	
	band = 'y'
	l = s._list_stronglines_in_band(band=band, threshold=0.2)
	assert set(l) == set(['NII6585', 'SII6718', 'SII6733'])
	

def test_spector_make_lineflux(spector1):
	s = spector1

	fn = s.dir_obj + 'spec_lineflux.csv'
	status = s.make_lineflux(lines=['Hb', 'OIII4960', 'OIII5008'], overwrite=False)

	assert status
	assert os.path.isfile(fn)

	tab = at.Table.read(fn, format='ascii.csv', comment='#')

	assert tab['f_OIII5008'][0] > tab['f_OIII4960'][0]

	f, ferr = s._get_line_flux_sdss(line='OIII5008', wunit=False)

	assert np.absolute(f-tab['f_OIII5008'][0]) / f < 0.05
	print('sdss ferr', ferr)
	print('my ferr', tab['ferr_OIII5008'][0])
	assert np.absolute(ferr-tab['ferr_OIII5008'][0]) / ferr < 0.1

	# currently lines other than hb, OIII, are not supported
	with pytest.raises(Exception):
		status = s.make_lineflux(lines=['Ha', 'Hb', 'OIII4960', 'OIII5008'], overwrite=True)


def test_spector_get_line_flux(spector1):
	s = spector1

	s.make_lineflux(overwrite=True)
	f_sdss, __ = s._get_line_flux_sdss(line='OIII5008', wunit=True)
	assert f_sdss.unit == u.Unit("1E-17 erg cm-2 s-1")


	f_sdss, __ = s._get_line_flux_sdss(line='OIII5008', wunit=False)
	npt.assert_almost_equal(f_sdss, 499.73093, decimal=1)


	for line in ['NeIII3870', 'NeIII3969', 'Hg', 'Hb', 'OIII4960', 'OIII5008']:
		f_sdss, f_sdss_err = s._get_line_flux_sdss(line=line, wunit=False)
		f, f_err = s._get_line_flux(line=line, wunit=False)

		assert np.absolute(f-f_sdss)/f < 0.50
		assert np.absolute(f_err-f_sdss_err)/f < 0.50


def test_spector_make_linefrac(spector1):
	s = spector1

	fn = s.dir_obj + 'spec_linefrac.csv'
	status = s.make_linefrac(band='i', tofixOIIIratio=True, overwrite=True)

	assert status
	assert os.path.isfile(fn)

	tab = at.Table.read(fn, format='ascii.csv', comment='#')

	assert tab['lineband'][0] == 'i'
	assert 'frac_OIII5008' in tab.colnames
	assert 'frac_OIII4960' in tab.colnames

	assert (tab['frac_OIII5008'] + tab['frac_OIII4960']) > 0.5
	assert (tab['frac_OIII5008'] + tab['frac_OIII4960']) < 1.
	assert tab['frac_OIII5008'] == tab['frac_OIII4960']*2.98 


def test_spector_calc_fline_over_fnuband(spector1):
	s = spector1

	status = s.make_linefrac(band='i', overwrite=False)

	frac_oiii = s._get_line_frac(band='i', line='OIII5008')

	with pytest.raises(Exception):
		frac_oiii = s._get_line_frac(band='r', line='OIII5008')

	r = s.calc_fline_over_fnuband(band='i', line='OIII5008')

	assert r.unit == u.Hz

	with pytest.raises(Exception):
		r = s.calc_fline_over_fnuband(band='i', line='Ha')


