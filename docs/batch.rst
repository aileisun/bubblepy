*****
Batch
*****

``batch`` takes care of operations done to a sample of objects. It has three basic functions: ``build()``, ``iterlist()``, and ``compile_table()``. The batch class is still under construction. Please use ``hscBatch`` for now. 


Batch
=====

Create Batch
------------

To create a batch one needs to provide a directory path ``dir_batch`` (string), a sample catalog ``catalog`` (astropy table), and the survey of the sample ``survey`` (string). 

	>>> from bubbleimg.batch import Batch
	>>> from astropy.io import ascii
	>>> dir_batch = 'here/my_batch/'
	>>> lines = ['    ra       dec    ', 
				'--------- ----------', 
				'29.158592 -4.0001336', 
				'29.748938 -6.4643413', 
				'30.410525 -6.3772438', ]

	>>> catalog = ascii.read(lines)
	>>> survey = 'hsc'
	>>> b = Batch(dir_batch=dir_batch, catalog=catalog, survey=survey)

Alternatively, one can provide a path to a fits file that contains the catalog table instead of the catalog itself. 

	>>> fn_cat = 'catalog.fits'
	>>> b = Batch(dir_batch=dir_batch, fn_cat=fn_cat, survey=survey)


The catalog table should contain at least two columns ``ra``, ``dec``, representing the coordinates of the objects in degree (decimal J2000). 

The name of the batch will be assigned to be the last directory of ``dir_batch``. 

	>>> b.name
	'my_batch'

One could also provide ``dir_parent`` and ``name`` instead of ``dir_batch``. 

	>>> dir_parent = 'here/'
	>>> name = 'my_batch'
	>>> b = Batch(dir_parent=dir_parent, catalog=catalog, survey=survey, name=name)
	>>> b.name
	'my_batch'
	>>> b.dir_batch
	'here/my_batch/'


One can check the list of objects of batch. 

	>>> b.list
	<Table length=3>
	    ra       dec        obj_name   
	 float64   float64       str64     
	--------- ---------- --------------
	29.158592 -4.0001336 SDSSJ0156-0400
	29.748938 -6.4643413 SDSSJ0158-0627
	30.410525 -6.3772438 SDSSJ0201-0622

By default the naming of the objects is SDSSJ plus the hhmmsddmm of the coordinates (sdss). The naming system can be changed using the argument ``obj_naming_sys``, but currently only sdss is supported. 

	>>> b = Batch(dir_batch=dir_batch, fn_cat=fn_cat, survey=survey, obj_naming_sys='sdss')


hscBatch
========

Create hscBatch
---------------

An ``hscBatch`` instance is created in the same way as ``Batch``. One does not need to set the ``survey`` argument and it's automatically set to ``'hsc'``. 

	>>> from bubbleimg.batch.hscbatch import hscBatch
	>>> dir_batch = 'here/my_batch/'
	>>> fn_cat = 'catalog.fits'
	>>> b = hscBatch(dir_batch=dir_batch, fn_cat=fn_cat)


Build hscBatch
--------------

Building the batch means to download the relevent data for each of the objects in the batch for the following analysis, and classify the objects into two classes: ``good`` and ``except``, where ``good`` objects have all the required files ready and ``except`` objects had problem getting all the files. 

One can do 

	>>> status = b.build()

By default, the ``bulid()`` function of hscBatch does the following steps to each of the objects: 

	- create an instance of hscimgLoader
		which tries to find an matching hsc counterpart 

	if that is successful then:
		- downlaod the 5 band stamp cutout images
		- download the 5 band psf
		- make a false color image of the stamp cutout
		- tries to find an sdss counterpart
		- download sdss spectrum


If the building was successful then the returning status is True. 
	>>> status
	True

If all the relevent files are successfully downloaded for an object, it will be inlcuded in the ``list_good`` list. (Here is just an example)

	>>> b.list_good
	<Table length=1>
	    ra       dec        obj_name   
	 float64   float64       str64     
	--------- ---------- --------------
	29.158592 -4.0001336 SDSSJ0156-0400

The object directories will be stored under dir_obj/good/. 

Otherwise it will be in the ``list_except`` list. 

	>>> b.list_except
	<Table length=2>
	    ra       dec        obj_name   
	 float64   float64       str64     
	--------- ---------- --------------
	29.748938 -6.4643413 SDSSJ0158-0627
	30.410525 -6.3772438 SDSSJ0201-0622

The object directories will be stored under dir_obj/except/. 


If you want to do the downloading again and overwrite the previously downloaded files. Do

	>>> status = b.build(overwrite=True)


Change how hscBatch is built
----------------------------

The default building setting is specified by the in ``self._func_build()`` of ``hscBatch``.

	>>>	def _func_build(self, obj, overwrite=False, **kwargs):
	>>>		"""
	>>>		Params
	>>>		------
	>>>		obj
	>>>		overwrite=False
	>>>	
	>>>		**kwargs:
	>>>			environment='iaa'
	>>>	
	>>>		Return
	>>>		------
	>>>		status
	>>>		"""
	>>>	
	>>>		# setting
	>>>		environment = kwargs.pop('environment', 'iaa')
	>>>		humvi_bands = 'riz'
	>>>	
	>>>		# running
	>>>		L = imgdownload.hscimgLoader(obj=obj, environment=environment, **kwargs)
	>>>	
	>>>		if L.status:
	>>>			statuss = 	[ 
	>>>						L.make_stamps(overwrite=overwrite), 
	>>>						L.make_psfs(overwrite=overwrite), 
	>>>						L.plot_colorimg(bands=humvi_bands, img_type='stamp', overwrite=overwrite)
	>>>						L.add_obj_sdss(), 
	>>>						L.obj.sdss.make_spec(overwrite=overwrite),
	>>>						]
	>>>	
	>>>			return all(statuss)
	>>>		else:
	>>>			return False


One can change how it's built by writing one's own ``func_build()``. This function has to take ``obj`` (instance of obsObj), see documentation for obsobj, and ``overwrite`` (bool), which specify whether to overwrite the downloaded files, as input arguments, and optionally other arguments as ``**kwargs``. This function has to return ``status`` to indicate whether the building of an object was successful. 

For example, one can define a very simple ``func_build()``,

	>>>	def func_build(self, obj, overwrite=False):
	>>>		"""
	>>>		Params
	>>>		------
	>>>		obj
	>>>		overwrite=False
	>>>	
	>>>		Return
	>>>		------
	>>>		status
	>>>		"""
	>>>		status = obj.add_hsc()
	>>>
	>>>		return status

which only tries to find an hsc counterpart and stores its info as hsc_xid.csv. 

To run it, one can do 
	>>> status = b.build(func_build)