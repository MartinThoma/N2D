# Not Too Deep Clustering

This is a library implementation of [n2d](https://github.com/rymc/n2d). To learn more about N2D, and clustering manifolds of autoencoded embeddings, please refer to the [amazing paper](https://arxiv.org/abs/1908.05968) published August 2019.

## What is it?

Not too deep clustering is a state of the art "deep" clustering technique, in which first, the data is embedded using an autoencoder. Then, instead of clustering that using some deep clustering network, we use a manifold learner to find the underlying (local) manifold in the embedding. Then, we cluster that manifold. In the paper, this was shown to produce high quality clusters without the standard extreme feature engineering required for clustering.

In this repository, a framework for A) reproducing the study and B) extending the study is given, for further research and use in a variety of applications

# Usage

First, lets load in some data. In this example, we will use the Human Activity Recognition(HAR) dataset. In this dataset, sets of time series with data from mobile devices is used to classify what the person is doing (walking, sitting, etc.)

```python
import datasets as data
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
tf.set_random_seed(0)
np.random.seed(0)

if len(K.tensorflow_backend._get_available_gpus()) > 0:
    print("Using GPU")
    session_conf = tf.ConfigProto(intra_op_parallelism_threads=1,
                                  inter_op_parallelism_threads=1,
                                  )
    sess = tf.Session(graph=tf.get_default_graph(), config=session_conf)
    K.set_session(sess)
```

Finally, we are ready to get clustering!

```python
import n2d as nd

n_clusters = 6  #there are 6 classes in HAR

# Initialize everything
harcluster = nd.n2d(x, nclust = n_clusters)
```

The first step in using this framework is to initialize an n2d object with the dataset and the number of clusters. The primary purpose of this step is to set up the autoencoder for training.

Next, we pretrain the autoencoder. In this step, you can fiddle with batch size etc. On the first run of the autoencoder, we want to include the weight_id parameter, which saves the weights in `weights/`, so we do not have to train the autoencoder repeatedly during our experiments.

```python
harcluster.preTrainEncoder(weight_id = "har")
```

The next time we want to use this autoencoder, we will instead use the weights argument:

```python
harcluster.preTrainEncoder(weights = "har-1000-ae_weights.h5")
```

The next important step is to define the 
