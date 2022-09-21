# ambientGAN for generating synthetic training data for learning quantitative photoacoustic tomography
## Introduction
In principle, photoacoustic images can be used to acquire information about the 3D spatial distribution of blood oxygen saturation values in a tissue. This information is useful for staging cancers, and monitoring tumour therapies. However, an ill-posed nonlinear inverse problem stands in the way of acquiring this information from real tissues. Model-based inversion techniques are commonly used to estimate sO2, though, these rely on having prior knowledge of certain tissue properties and a precise/accurate model of image acquisition. In practice, this information is challenging to acquire, limiting its applicability to artificial phantoms.
Recently, in silico results (and limited results from real tissues) have shown that networks can be trained to learn a model for sO2 quantification without explicit prior knowledge of model parameters. Though, supervised learning methods require extensive 'paired' datasets, that are highly challenging to acquire in practice.
Although ample simulated data can be produced for training networks, these ultimately do not contain the same kinds/frequency of features (and relation between features and sO2) as real images. As a consequence, networks trained on this data can not be used to accurately estimate sO2 from real images.   

## Method
Working toward generating synthetic training data for sO2 quantification (photoacoustic image + underlying optical absorption and scattering distribution), we attempt to generate synthetic versions of  simulated photoacoustic images and their corresponding absorption distribution using an ambientGAN. 
Here, a WGAN-GP framework is modified to include a pretrained (and fixed) light model appending the generator. Therefore, the network generates an input to a light model (i.e. generates an absorption distribution) that produces an image indistinguishable from the GAN’s training set of simulated images. 
Training set: images of circular absorbers of varying sizes in non-scattering homogenous tissue produced with simulated light model. 
Light model network: trained to map ‘image’ of absorption coefficient to absorbed optical energy (i.e. learns the light model). Once trained, its weights are frozen. 

## Repo notes
This repo contains network code, the training data for the light model network, results, and some ambientGAN training examples. 

The variables mua_volumes and p0_volumes are stored as distinct files in this repo (instead of belonging to the same variable ‘fluence_train_data.mat’) to simplify storage.

ambient_GAN_fluence_net_train_fluence_net.py is run first to train the light model network. Then, ambient_GAN_fluence_net_train_wgan.py is run to train the network. 

## Further information
More information can be found in my PhD thesis: [here](https://discovery.ucl.ac.uk/id/eprint/10148082/) 





