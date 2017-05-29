# loader.py 
# ALS 2017/05/02

import numpy as np
import astropy.table as at
import astropy.units as u
import os 
import abc
from catalogue.catalogue_util import getSDSSName_fromRADEC

from ..filters import surveysetup
from ..obsobj import obsObj
# from ..class_obsobj import obsobj


class imgLoader(object):
	__metaclass__ = abc.ABCMeta

	def __init__(self, **kwargs):
		"""
		imgLoader

		Params
		----------
		/either
			obj (object of class obsobj): with attributes ra, dec, dir_obj
		/or  
			ra (float)
			dec (float)
			/either
				dir_obj (string)
			/or 
				dir_parent (string): attr dir_obj is set to dir_parent+'SDSSJXXXX+XXXX/'
				
		img_width (angle quantity or int) = 20 * u.arcsec:
			:if int then unit is assumed to be pix. 

		img_height (angle quantity or int) = 20 * u.arcsec:

		user = '': account user name for access
		password = '': account password for access

		Attributes
		----------
		ra (float)
		dec (float)
		dir_obj (string)
		img_width (angle quantity)
		img_height (angle quantity)
		img_width_pix (quantity of unit u.pix): floor integer of img_width in pixels
		img_height_pix (quantity of unit u.pix): floor integer of img_width in pixels

		obj (optional) may have attributes sdss.xid etc 

		"""
		#===== unparse input
		print "WARNING: to reorganize loader init using plainobj"
		
		if 'obj' in kwargs: 
			self.obj = kwargs.pop('obj')
			# sanity check
			if 'dir_obj' in kwargs:
				if self.obj.dir_obj != kwargs.pop('dir_obj'):
					raise Exception("[loader] conflicting dir_obj entered")
		else: 
			self.obj = obsObj(**kwargs)
		# else:
		# 	raise TypeError('dir_obj or dir_parent not specified')

		self.ra = self.obj.ra
		self.dec = self.obj.dec
		self.dir_obj = self.obj.dir_obj

		# self.ra = kwargs.pop('ra', None)
		# self.dec = kwargs.pop('dec', None)
		# if 'dir_obj' in kwargs:
		# 	self.dir_obj = kwargs.pop('dir_obj', None)
		# elif 'dir_parent' in kwargs:
		# 	sdssname = getSDSSName_fromRADEC(self.ra, self.dec)
		# 	self.dir_parent = kwargs.pop('dir_parent', '')
		# 	self.dir_obj = self.dir_parent+sdssname+'/'
		# else:
		# 	raise TypeError('dir_obj or dir_parent not specified')

		self.img_width = kwargs.pop('img_width', 20*u.arcsec)
		self.img_height = kwargs.pop('img_height', 20*u.arcsec)
		self._user = kwargs.pop('user', "")
		self._password = kwargs.pop('password', "")

		if (self.ra is None) or (self.dec is None) or (self.dir_obj is None):
			raise TypeError('ra or dec or dir_obj not specified')
		
		self._attach_img_widthheight_unit()
		self.survey = 'to be overwritten'
		self.pixsize = -1


	@abc.abstractmethod
	def make_stamps(self, **kwargs):
		raise NotImplementedError("Subclass must implement abstract method")


	@abc.abstractmethod
	def make_psfs(self, **kwargs):
		raise NotImplementedError("Subclass must implement abstract method")


	def get_stamp_filepath(self, band):
		return self.dir_obj+self.get_stamp_filename(band)


	def get_stamp_filename(self, band):
		return 'stamp-{0}.fits'.format(band)


	def get_psf_filepath(self, band):
		return self.dir_obj+self.get_psf_filename(band)


	def get_psf_filename(self, band):
		return 'psf-{0}.fits'.format(band)


	# def _imgLoader__make_stamp_core(self, func_download_stamp, **kwargs):
	# 	"""
	# 	make a stamp of self and of band
	# 	call _download_stamp and takes care of overwrite with argument 'overwrite'. Default: do not overwrite. 

	# 	Params
	# 	----------
	# 	func_download_stamp (function)
	# 	band (string) = 'r'
	# 	overwrite (boolean) = False
	# 	**kwargs to be entered into func_download_stamp()

	# 	Return
	# 	----------
	# 	status: True if downloaded or skipped, False if download fails
	# 	"""
	# 	band = kwargs.pop('band', 'r')
	# 	overwrite = kwargs.pop('overwrite', False)

	# 	# setting
	# 	filename = self.get_stamp_filename(band)
	# 	file = self.get_stamp_filepath(band)

	# 	if not os.path.isdir(self.dir_obj):
	# 	    os.makedirs(self.dir_obj)

	# 	if (not os.path.isfile(file)) or overwrite:
	# 		print "download_stamp() ".format(filename)
	# 		try: 
	# 			return func_download_stamp(band=band, **kwargs) # if failed then return False
	# 		except:
	# 			return False
	# 	else:
	# 		print "skip download_stamp() as file {0} exists".format(filename)
	# 		return True


	# def _imgLoader__make_stamps_core(self, func_download_stamp, **kwargs):
	# 	"""
	# 	make all stamp images of all survey bands for obj self. 

	# 	Params
	# 	----------
	# 	func_download_stamp (function)
	# 	overwrite (boolean) = False
	# 	**kwargs to be entered into func_download_stamp()

	# 	Return
	# 	----------
	# 	status: True if all downloaded or skipped, False if any of the downloads fails
	# 	"""
	# 	bands = surveysetup.surveybands[self.survey]

	# 	statuss = np.ndarray(5, dtype=bool)
	# 	for i, band in enumerate(bands): 
	# 		statuss[i] = self._imgLoader__make_stamp_core(func_download_stamp=func_download_stamp, band=band, **kwargs)

	# 	return all(statuss)


	def _imgLoader__make_file_core(self, func_download_file, func_naming_file, band='r', overwrite=False, **kwargs):
		"""
		make a file of self and of band
		call _download_file and takes care of overwrite with argument 'overwrite'. Default: do not overwrite. 

		Params
		----------
		func_download_file (function), which takes (self, band) as argument
		func_naming_file (function), which takes (self, band) as argument
		band (string) = 'r'
		overwrite (boolean) = False
		**kwargs to be entered into func_download_file()

		Return
		----------
		status: True if downloaded or skipped, False if download fails
		"""

		# setting
		filename = func_naming_file(band)
		filepath = self.dir_obj+filename

		if not os.path.isdir(self.dir_obj):
		    os.makedirs(self.dir_obj)

		if (not os.path.isfile(filepath)) or overwrite:
			print "download_file() ".format(filename)
			# try: 
			return func_download_file(band=band, **kwargs) # if failed then return False
			# except:
				# return False
			
		else:
			print "skip download_file() as file {0} exists".format(filename)
			return True


	def _imgLoader__make_files_core(self, func_download_file, func_naming_file, overwrite=False, **kwargs):
		"""
		make all file images of all survey bands for obj self. 

		Params
		----------
		func_download_file (function), which takes (self, band) as argument
		func_naming_file (function), which takes (self, band) as argument
		overwrite (boolean) = False
		**kwargs to be entered into func_download_file()

		Return
		----------
		status: True if all downloaded or skipped, False if any of the downloads fails
		"""
		bands = surveysetup.surveybands[self.survey]

		statuss = np.ndarray(len(bands), dtype=bool)
		for i, band in enumerate(bands): 
			statuss[i] = self._imgLoader__make_file_core(func_download_file=func_download_file, func_naming_file=func_naming_file, band=band, overwrite=overwrite, **kwargs)

		return all(statuss)


	def _attach_img_widthheight_unit(self):
		""" 
		make sure that self.img_width and self.height has angular unit 
		If they are a int/whole number then attach unit u.pix. otherwise raise error. 
		"""
		if not hasattr(self.img_width, 'unit'):
			if type(self.img_width) is int:
				self.img_width *= u.pix
				print "Assuming img_width unit is pix"
			elif type(self.img_width) is float and (self.img_width).is_integer():
				self.img_width *= u.pix
				print "Assuming img_width unit is pix"
			else: 
				raise ValueError("Param img_width has to be angular quantity or a whole number for pix")

		if not hasattr(self.img_height, 'unit'):
			if type(self.img_height) is int:
				self.img_height *= u.pix
				print "Assuming img_height unit is pix"
			elif type(self.img_height) is float and (self.img_height).is_integer():
				self.img_height *= u.pix
				print "Assuming img_height unit is pix"
			else: 
				raise ValueError("Param img_height has to be angular quantity or a whole number for pix")


	def _add_attr_img_width_pix_arcsec(self):
		""" creating attributes 
		self.img_width_pix (int)
		self.img_height_pix (int)
		self.img_height_arcsec (angular quantity)
		self.img_width_arcsec (angular quantity)
		which are self.img_width and img_height but changed to indicated units """
		survey_pixelscale = u.pixel_scale(self.pixsize/u.pixel)

		if hasattr(self.img_width, 'unit'): 
			nwpix = (self.img_width.to(u.pix, survey_pixelscale)/u.pix).to(u.dimensionless_unscaled)
			self.img_width_pix = int(np.floor(nwpix))
			self.img_width_arcsec = self.img_width.to(u.arcsec, survey_pixelscale)
		else: 
			raise ValueError('self.img_width has no angular units')

		if hasattr(self.img_height, 'unit'): 
			nhpix = (self.img_height.to(u.pix, survey_pixelscale)/u.pix).to(u.dimensionless_unscaled)
			self.img_height_pix = int(np.floor(nhpix))
			self.img_height_arcsec = self.img_height.to(u.arcsec, survey_pixelscale)
		else: 
			raise ValueError('self.img_height has no angular units')


	def add_obj_sdss(self, update=False):
		""" 
		if self.obj does not exist create self.obj as an instance of obsObj
		if self.obj does not have sdss then call add_sdss(), which makes self.obj.sdss.xid, etc. 
		download xid.csv, photoobj.csv into directory dir_obj 

		Return
		------
		status: True if success, False if not
		"""
		if (not hasattr(self, 'obj')) or update:
			self.obj = obsObj(ra=self.ra, dec=self.dec, dir_obj=self.dir_obj)

		if (not hasattr(self.obj, 'sdss')) or update:
			status = self.obj.add_sdss()
		else: 
			status = True

		# sanity check
		if self.obj.dir_obj != self.dir_obj: 
			raise ValueError('self.dir_obj inconsistent with SDSS naming convension')

		return status


	def add_obj_hsc(self, update=False, **kwargs):
		""" 
		if self.obj does not exist create self.obj as an instance of obsObj
		if self.obj does not have hsc then call add_hsc(), which makes self.obj.hsc.xid, etc. 
		download xid.csv, photoobj.csv into directory dir_obj 

		Return
		------
		status: True if success, False if not
		"""
		if (not hasattr(self, 'obj')) or update:
			self.obj = obsObj(ra=self.ra, dec=self.dec, dir_obj=self.dir_obj)

		if (not hasattr(self.obj, 'hsc')) or update:
			status = self.obj.add_hsc(**kwargs)

		# sanity check
		if self.obj.dir_obj != self.dir_obj: 
			raise ValueError('self.dir_obj inconsistent with SDSS naming convension')

		return status