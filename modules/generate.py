#!/usr/bin/env python3

def generate_ds_MNIST( max_ind, class_labels, crop, downsample_rate, downsample_method,
inds_to_ave, pixel_sum, inds_to_calc_RF, num_features, screen_size, save_results_folder,
show_thumbnails ):

	'''
	Loads the MNIST dataset (from Yann LeCun's website),
	then applies various preprocessing steps to reduce the number of pixels
	(each pixel will be a feature).

	The 'receptive field' step destroys spatial relationships, so to reconstruct
	a 12 x 12 thumbnail (eg for viewing, or for CNN use) the active pixel indices
	can be embedded in a 144 x 1 col vector of zeros, then reshaped into a 12 x 12 image.
	Modify the path for the MNIST data file as needed.

	Inputs (preprocessing parameters):
		max_ind, class_labels, crop,
		downsample_rate: downsample ratio
		downsample_method: method for downsampling image

		inds_to_ave, pixel_sum, inds_to_calc_RF,

		num_features: number of pixels in the receptive field

		screen_size: screen size (width, height) for images

		save_results_folder,

		show_thumbnails: number of thumbnails to show for each class (0 means none)

	Outputs:
		1. featureArray = n x m x 10 array. n = #active pixels, m = #digits from
			each class that will be used.
			The 3rd dimension gives the class, 1:10 where 10 = '0'.
		2. activePixelInds: list of pixel indices to allow re-embedding into empty
			thumbnail for viewing.
	  	3. lengthOfSide: allows reconstruction of thumbnails given from the
			feature vectors.
	#---------------------------------------------------------------------------
	Preprocessing includes:
		1. Load MNIST set.generateDownsampledMnistSet_fn
		2. cropping and downsampling
		3. mean-subtract, make non-negative, normalize pixel sums
		4. select active pixels (receptive field)
	Copyright (c) 2019 Adam P. Jones (ajones173@gmail.com) and Charles B. Delahunt (delahunt@uw.edu)
	MIT License
	'''

	import os
	import numpy as np
	from modules.extract import extractMNISTFeatureArray
	from modules.extract import cropDownsampleVectorizeImageStack
	from modules.extract import averageImageStack
	from modules.extract import selectActivePixels

	im_dir = 'MNIST_all'

	mnist_fname = os.getcwd() + os.sep + im_dir + os.sep + 'MNIST_all.npy'

	# test for npy file before loading. run creation script, if absent.
	if not os.path.isfile(mnist_fname):
		# download and save data from the web
		from MNIST_all import MNIST_makeAll
		MNIST_makeAll.download_save()

	# 1. extract mnist:
	mnist = np.load(mnist_fname, allow_pickle = True).item()
	# loads dictionary 'mnist' with keys:value pairs =
	#              .train_images, .test_images, .train_labels, .test_labels (ie the original data from PMTK3)
	#              AND parsed by class. These fields are used to assemble the imageArray:
	#              .trI_* = train_images of class *
	#              .teI_* = test_images of class *
	#              .trL_* = train_labels of class *
	#              .teL_* = test_labels of class *

	# extract the required images and classes
	imageIndices = range(max_ind+1)
	imageArray = extractMNISTFeatureArray(mnist, class_labels, imageIndices, 'train')
	# imageArray = numberImages x h x w x numberClasses 4-D array. class order: 1 to 10 (10 = '0')

	# calc new dimensions
	im_z, im_height, im_width, label_len = imageArray.shape
	cropVal = crop*np.ones(4,dtype = int)
	new_width = (im_width-np.sum(cropVal[2:]))/downsample_rate
	new_height = (im_height-np.sum(cropVal[0:2]))/downsample_rate
	new_length = int(new_width*new_height)

	featureArray = np.zeros((new_length, im_z, label_len)) # pre-allocate

	# crop, downsample, and vectorize the average images and the image stacks
	for c in range(label_len):
		# featureArray[...,n] : [a x numImages] array,
		# 	where a = number of pixels in the cropped and downsampled images
		featureArray[...,c] = cropDownsampleVectorizeImageStack(imageArray[...,c],
		 	crop, downsample_rate, downsample_method)

	del imageArray # to save memory

	# subtract a mean image from all feature vectors, then make values non-negative

	# a. Make an overall average feature vector, using the samples specified in 'indsToAverage'
	overallAve = np.zeros((new_length, )) # pre-allocate col vector
	classAvesRaw = np.zeros((new_length, label_len))
	for c in range(label_len):
		classAvesRaw[:,c] = averageImageStack(featureArray[:, inds_to_ave, c],
			list(range(len(inds_to_ave))) )
		overallAve += classAvesRaw[:,c]
	overallAve /= label_len

	# b. Subtract this overallAve image from all images
	ave_2D = np.tile(overallAve,(im_z,1)).T
	ave_3D = np.repeat(ave_2D[:,:,np.newaxis],label_len,2)
	featureArray -= ave_3D
	del ave_2D, ave_3D

	featureArray = np.maximum( featureArray, 0 ) # remove any negative pixel values

	# c. Normalize each image so the pixels sum to the same amount
	fSums = np.sum(featureArray, axis=0)
	normArray = np.repeat(fSums[np.newaxis,:,:],new_length,0)
	featureArray *= pixel_sum
	featureArray /= normArray
	# featureArray now consists of mean-subtracted, non-negative,
	# normalized (by sum of pixels) columns, each column a vectorized thumbnail.
	# size = 144 x numDigitsPerClass x 10

	lengthOfSide = new_length # save to allow sde_EM_evolution to print thumbnails.

	# d. Define a Receptive Field, ie the active pixels
	# Reduce the number of features by getting rid of less-active pixels.
	# If we are using an existing moth then activePixelInds is already defined, so
	# we need to load the modelParams to get the number of features
	# (since this is defined by the AL architecture):

	# reduce pixel number (downsample) to reflect # of features in moth brain
	fA_sub = featureArray[:, inds_to_calc_RF, :]
	activePixelInds = selectActivePixels(fA_sub, num_features,
		screen_size, save_image_folder=save_results_folder,
		show_thumbnails=show_thumbnails)
	featureArray = featureArray[activePixelInds,:,:].squeeze() # Project onto the active pixels

	return featureArray, activePixelInds, lengthOfSide

# MIT license:
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial
# portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN
# AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.