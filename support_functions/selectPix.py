def selectActivePixels( featureArray, numFeatures, saveImageFolder=[],
    scrsz = (1920, 1080), showThumbnails = 0 ):
    '''
    Select the most active pixels, considering all class average images, to use as features.
    Inputs:
        1. featureArray: 3-D array nF x nS x nC, where nF = # of features,
        nS = # samples per class, nC = number of classes. As created by genDS_MNIST.
        2. numFeatures: The number of active pixels to use (these form the receptive field).
        3. saveImageFolder: dir to save average class images, empty = don't save
        4. screensize: (width, height)
        5. showThumbnails: number of thumbnails to plot
    Output:
        1. activePixelInds: 1 x nF vector of indices to use as features.
        Indices are relative to the vectorized thumbnails (so between 1 and 144).

    Copyright (c) 2019 Adam P. Jones (ajones173@gmail.com) and Charles B. Delahunt (delahunt@uw.edu)
    MIT License
    '''

    # make a classAves matrix (cA), each col a class ave 1 to 10 (ie 0),
    #  and add a col for the overallAve
    import numpy as np
    from support_functions.aveImStack import averageImageStack
    from support_functions.show_figs import showFeatureArrayThumbnails

    pixNum, numPerClass, classNum  = featureArray.shape
    cA = np.zeros((pixNum, classNum+1))

    for i in range(classNum):

        cA[:,i] = averageImageStack(featureArray[:,:,i], list(range(numPerClass)))

    # last col = average image over all digits
    cA[:,-1] = np.sum(cA[:,:-1], axis=1) / classNum

    # normed version (does not rescale the overall average)
    z = np.max(cA, axis=0)
    z[-1] = 1
    caNormed = cA/np.tile(z, (pixNum,1))
    # num = size(caNormed,2);

    # select most active 'numFeatures' pixels
    this = cA[:, :-1]

    thisLogical = np.zeros(this.shape)

    # all the pixel values from all the class averages, in descending order
    vals = np.sort(this.flatten())[::-1]

    # start selecting the highest-valued pixels
    stop = 0
    while not stop:
        thresh = vals.max()
        thisLogical[this>=thresh] = 1
        activePixels = thisLogical.sum(axis=1) # sum the rows
        # If a class ave had the i'th pixel, selected, keptPixels(i) > 0
        stop = (activePixels > 0).sum() >= numFeatures # check if we have enough pixels

        vals = vals[vals < thresh]  # peel off the value(s) just used

    activePixelInds = np.nonzero(activePixels > 0)[0]

    if showThumbnails and saveImageFolder:
        # plot the normalized classAves pre-ablation
        normalize = 0
        titleStr = 'class aves, all pixels'
        showFeatureArrayThumbnails(caNormed, classNum+1, normalize, titleStr,
            scrsz, saveImageFolder, 'all')

        # look at active pixels of the classAves, ie post-ablation
        normalize = 0
        caActiveOnly = np.zeros(caNormed.shape)
        caActiveOnly[activePixelInds, : ] = caNormed[activePixelInds, :]
        titleStr = 'class aves, active pixels only'

        showFeatureArrayThumbnails(caActiveOnly, classNum+1, normalize, titleStr,
            scrsz, saveImageFolder, 'active')

    return activePixelInds

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
