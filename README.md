[![Documentation Status](https://readthedocs.org/projects/n2d/badge/?version=latest)](https://n2d.readthedocs.io/en/latest/?badge=latest)

Welcome to the extensible autoencoder branch of N2D! Here we will make the autoencoders more easily extensible, without the %d sort of API


# Changes

Sklearn-like API. Please note this is a major update, and if you are using a previous version you will have to change your code, as the API has changed!


# Not Too Deep Clustering

This is a library implementation of [n2d](https://github.com/rymc/n2d). To learn more about N2D, and clustering manifolds of autoencoded embeddings, please refer to the [amazing paper](https://arxiv.org/abs/1908.05968) published August 2019.

## What is it?

Not too deep clustering is a state of the art "deep" clustering technique, in which first, the data is embedded using an autoencoder. Then, instead of clustering that using some deep clustering network, we use a manifold learner to find the underlying (local) manifold in the embedding. Then, we cluster that manifold. In the paper, this was shown to produce high quality clusters without the standard extreme feature engineering required for clustering.

In this repository, a framework for A) reproducing the study and B) extending the study is given, for further research and use in a variety of applications

# Documentation

Full documentation is available on [read the docs](https://n2d.readthedocs.io/en/latest/)

# Installation

N2D is [available on pypi](https://pypi.org/project/n2d/)

```sh
pip install n2d
```

# Usage

First, lets load in some data. In this example, we will use the Human Activity Recognition(HAR) dataset. In this dataset, sets of time series with data from mobile devices is used to classify what the person is doing (walking, sitting, etc.)

```python
from n2d import datasets as data
x,y, y_names = data.load_har()
```

Next, lets set up our deep learning environment, as well as load in necessary libraries:

```python
import os
import random as rn
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
plt.style.use(['seaborn-white', 'seaborn-paper'])
sns.set_context("paper", font_scale=1.3)
matplotlib.use('agg')

import tensorflow as tf
from keras import backend as K

# set up environment
os.environ['PYTHONHASHSEED'] = '0'


rn.seed(0)

np.random.seed(0)
```

Finally, we are ready to get clustering!

First, we need to define the manifold learning and clustering algorithm which we will use to cluster the autoencoded embedding. In general, it is best to use UmapGMM, which in the paper gave the absolute best performance.

```python
import n2d as nd

n_clusters = 6  #there are 6 classes in HAR

manifoldGMM = n2d.UmapGMM(n_clusters)
```

The next step in this framework is to initialize the n2d object, which builds an autoencoder network and gets everything ready for clustering:

```python
harcluster = n2d.n2d(x,manifoldGMM, ndim = n_clusters)
```

Next, we fit the data. In this step, the autoencoder is trained on the data, setting up weights.

```python
harcluster.fit(weight_id = "har")
```

The next time we want to use this autoencoder, we will instead use the weights argument:

```python
harcluster.fit(weights = "har-1000-ae_weights.h5")
```

Now we can make a prediction, as well as visualize and assess. In this step, the manifold learner learns the manifold for the data, which is then clustered. By default, it makes the prediction on the data stored internally, however you can specify a new `x` in order to make predictions on new data.

```python
harcluster.predict()
# predictions are stored in harcluster.preds
harcluster.visualize(y, y_names, savePath = "viz/har", nclust = n_clusters)
print(harcluster.assess(y))
# (0.81212, 0.71669, 0.64013)
```

Before viewing the results, lets talk about the metrics. The first metric is cluster accuracy, which we see here is 81.2%, which is absolutely state of the art for the HAR dataset. The next metric is NMI, which is another metric which describes cluster quality based on labels, independent of the number of clusters. We have an NMI of 0.717, which is again absolutely state of the art for this dataset. The last metric, ARI, shows another comparison between the actual groupings and our grouping. A value of 1 means the groupings are nearly the same, while a value of 0 means they completely disagree. We have a value of 0.64013, which indicates that are predictions are more or less in agreement with the truth, however they are not perfect.

![N2D prediction](https://i.imgur.com/91iwVVj.png)

N2D prediction

![](https://i.imgur.com/8PTPTmE.png)
Actual clusters

## Extending

### Replacing the manifold clustering mechanism

So far, this framework only includes the method for manifold clustering which the authors of the paper deemed best, umap with gaussian mixture clustering. Lets say however we want to try out spectral clustering instead:

```python
from sklearn.cluster import SpectralClustering
import umap
class UmapSpectral:
    def __init__(self, nclust,
                 umapdim = 2,
                 umapN = 10,
                 umapMd = float(0),
                 umapMetric = 'euclidean',
		 random_state = 0
                 ):
        self.nclust = nclust
	# change this bit for changing the manifold learner
        self.manifoldInEmbedding = umap.UMAP(
            random_state = random_state,
            metric = umapMetric,
            n_components = umapdim,
            n_neighbors = umapN,
            min_dist = umapMd
        )
	# change this bit to change the clustering mechanism
	self.clusterManifold = SpectralClustering(
		n_clusters = nclust,
		affinity = 'nearest_neighbors',
		random_state = random_state
	)

	self.hle = None


    def fit(self, hl):
        self.hle = self.manifoldInEmbedding.fit_transform(hl)
        self.clusterManifold.fit(self.hle)

    def predict(self):
    # obviously if you change the clustering method or the manifold learner
    # youll want to change the predict method too.
	y_pred = self.clusterManifold.fit_predict(self.hle)
        return(y_pred)
```

Now we can run and assess our new clustering method:

```python
manifoldSC = UmapSpectral(6)
SCclust = n2d.n2d(x, manifoldSC, ndim = n_clusters)
# weights from the examples folder
SCclust.fit(weights = "weights/har-1000-ae_weights.h5")
SCclust.predict()
print(SCclust.assess(y))
# (0.40946, 0.42137, 0.14973)
```

This clearly did not go as well, however we can see that it is very easy to extend this library. We could also try out swapping UMAP for ISOMAP, the clustering method with kmeans, or maybe with a deep clustering technique. 

### Replacing the embedding mechanism

We can also replace the embedding learner, by writing a new class. In this example we will implement a denoising autoencoder, as demonstrated in [this awesome blog post](https://blog.keras.io/building-autoencoders-in-keras.html)

```python
import os
import n2d
from n2d import datasets as data
import random as rn
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
plt.style.use(['seaborn-white', 'seaborn-paper'])
sns.set_context("paper", font_scale=1.3)
matplotlib.use('agg')
import tensorflow as tf
from keras import backend as K
import sys
from keras.layers import Dense, Input
from keras.models import Model

x,y, y_names = data.load_fashion()


class denoisingAutoEncoder:
    def __init__(self, data, ndim, architecture, 
    noise_factor = 0.5, act = 'relu'):
        dims = [data.shape[-1]] + architecture + [ndim]
        self.dims = dims
        self.noise_factor = noise_factor
        self.act = act
        self.x = Input(shape = (dims[0],), name = 'input')
        self.h = self.x
        n_stacks = len(self.dims) - 1
        for i in range(n_stacks - 1):
            self.h = Dense(self.dims[i + 1], activation = self.act, name = 'encoder_%d' %i)(self.h)
	# this is open to suggestion for better methods of saving the embedding
        self.h = Dense(self.dims[-1], name = 'encoder_%d' % (n_stacks -1))(self.h)
        for i in range(n_stacks - 1, 0, -1):
            self.h = Dense(self.dims[i], activation = self.act, name = 'decoder_%d' % i )(self.h)
        self.h = Dense(dims[0], name = 'decoder_0')(self.h)

        self.Model = Model(inputs = self.x, outputs = self.h)

    def add_noise(self, x):
    	# this is the new bit
        x_clean = x
        x_noisy = x_clean + self.noise_factor * np.random.normal(loc = 0.0, scale = 1.0, size = x_clean.shape)
        x_noisy = np.clip(x_noisy, 0., 1.)

        return x_clean, x_noisy

    def fit(self, dataset, batch_size = 256, pretrain_epochs = 1000,
                     loss = 'mse', optimizer = 'adam',weights = None,
                     verbose = 0, weightname = 'fashion'):
        if weights == None:
            x, x_noisy = self.add_noise(dataset)
            self.Model.compile(
                loss = loss, optimizer = optimizer
            )
            self.Model.fit(
                x_noisy, x,
                batch_size = batch_size,
                epochs = pretrain_epochs
            )

            self.Model.save_weights("weights/" + weightname + "-" +
                                    str(pretrain_epochs) +
                                    "-ae_weights.h5")
        else:
            self.Model.load_weights(weights)


n_clusters = 10

model = n2d.n2d(x, manifoldLearner=n2d.UmapGMM(n_clusters),
	autoencoder = denoisingAutoEncoder, 
	ndim = n_clusters, ae_args={'noise_factor': 0.5})

model.fit(weight_id="fashion_denoise")

model.predict()

model.visualize(y, y_names, savePath = "viz/fashion_denoise", nclust = n_clusters)
print(model.assess(y))
```

Lets talk about the ingredients we need for modification:

The class needs to take in a list of dimensions for the model. These dimensions should only include the center layers (read, not input and output). If we want to change the model architecture, we simply put that as the `architecture` argunent of n2d:

```python
n2d.n2d(..., architecture = [500,500,2000])
```

This will design the networks to be [input dimensions, 500, 500, 2000, output dimensions], as seen in the denoisingAutoencoder class. If we want to change the autoencoder itself, we need to write a class which accepts the shape, and then some other (preferably with defaults) arguments. This class NEEDS to have a method called fit. Everything else is up to you! To add in extra arguments to whatever your new autoencoder is, you pass them in through a dict called ae_args, as seen in the above example.


# Roadmap

- [x] Package library
- [x] Package data
- [x] Early stopping
- [ ] Implement data augmentation techniques for images, sequences, and time series
- [x] Make autoencoder interchangeable just like the rest
- [ ] Simpler way to extract embedding
- [ ] Implement other types of autoencoders as well as convolutional layers
- [x] Manage file saving paths better
- [ ] Implement other promising methods
- [ ] Make assessment/visualization more extensible
- [x] Documentation?
- [x] Find an elegant way to deal with pre training weights
- [ ] Package on Nix
- [ ] Blog post?

# Contributing

N2D is a work in progress and is open to suggestions to make it faster, more extensible, and generally more usable. Please make an issue if you have any ideas of how to be more accessible and more usable! 


# Citation

If you use N2D in your research, please credit the original authors of the paper. Bibtex included below:

```
@article{2019arXiv190805968M,
  title = {N2D:(Not Too) Deep Clustering via Clustering the Local Manifold of an Autoencoded Embedding},
  author = {{McConville}, Ryan and {Santos-Rodriguez}, Raul and {Piechocki}, Robert J and {Craddock}, Ian},
  journal = {arXiv preprint arXiv:1908.05968},
  year = "2019",
}
```
