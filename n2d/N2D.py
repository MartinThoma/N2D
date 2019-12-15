import os
import random as rn

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

import pandas as pd
import numpy as np
import sys
import tensorflow as tf

from . import linear_assignment as la

import umap
from keras import backend as K
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.layers import Dense, Input
from keras.models import Model
from sklearn import metrics
from sklearn import mixture
from sklearn.cluster import KMeans, SpectralClustering
from sklearn.manifold import Isomap
from sklearn.manifold import LocallyLinearEmbedding

import pandas as pd

class AutoEncoder:
    """AutoeEncoder: standard feed forward autoencoder

    Parameters:
    -----------
    input_dim: int
        The number of dimensions of your input


    output_dim: int
        The number of dimensions which you wish to represent the data as.

    architecture: list
        The structure of the hidden architecture of the networks. for example,
        the n2d default is [500, 500, 2000],
        which means the encoder has the structure of:
        [input dim, 500, 500, 2000, ndim], and the decoder has the structure of:
        [ndim, 2000, 500, 500, input dim]

    act: string
        The activatin function. Defaults to 'relu'
    """
    def __init__(self, input_dim, output_dim, architecture, act = 'relu'):
        shape = [input_dim] + architecture + [ndim]
        self.dims = shape
        self.act = act
        self.x = Input(shape = (self.dims[0],), name = 'input')
        self.h = self.x
        n_stacks = len(self.dims) - 1
        for i in range(n_stacks - 1):
            self.h = Dense(self.dims[i + 1], activation = self.act, name = 'encoder_%d' %i)(self.h)
        self.encoder = Dense(self.dims[-1], name = 'encoder_%d' % (n_stacks -1))(self.h)
        self.decoded = Dense(self.dims[-2], name = 'decoder', activation = self.act)(self.encoder)
        for i in range(n_stacks - 2, 0, -1):
            self.decoded = Dense(self.dims[i], activation = self.act, name = 'decoder_%d' % i )(self.decoded)
        self.decoded = Dense(self.dims[0], name = 'decoder_0')(self.decoded)

        self.Model = Model(inputs = self.x, outputs = self.decoded)
        self.encoder = Model(inputs = self.x, outputs = self.encoder)

    def fit(self, x, batch_size = 256, pretrain_epochs = 1000,
                     loss = 'mse', optimizer = 'adam',weights = None,
                     verbose = 0, weight_id = 'fashion', patience = None):

        """fit: train the autoencoder.

            Parameters:
                -------------
                x: array-like
                the data you wish to fit

            batch_size: int
            the batch size

            pretrain_epochs: int
            number of epochs you wish to run.

            loss: string or function
            loss function. Defaults to mse

            optimizer: string or function
            optimizer. defaults to adam

            weights: string
            if weights is used, the path to the pretrained nn weights.

            verbose: int
            how verbose you wish the autoencoder to be while training.

            weight_id: string
            where you wish to save the weights

            patience: int
            if not None, the early stopping criterion
            """


        if weights == None:
            self.Model.compile(
                loss = loss, optimizer = optimizer
            )
            if patience is not None:
                callbacks = [EarlyStopping(monitor='loss', patience=patience),
                             ModelCheckpoint(filepath=weight_id,
                                             monitor='loss',
                                             save_best_only=True)]
            else:
                callbacks = [ModelCheckpoint(filepath = weight_id,
                                             monitor = 'loss',
                                             save_best_only = True)]
            self.Model.fit(
                x, x,
                batch_size = batch_size,
                epochs = pretrain_epochs,
                callbacks = callbacks, verbose = verbose
            )

            self.Model.save_weights(weight_id)
        else:
            self.Model.load_weights(weights)



class UmapGMM:
    """
        UmapGMM: UMAP gaussian mixing

            Parameters:
            ------------
            nclust: int
                the number of clusters

            umapdim: int
                number of dimensions to find with umap. Defaults to 2

            umapN: int
                Number of nearest neighbors to use for UMAP. Defaults to 10,
                20 is also a reasonable choice

            umapMd: float
                minimum distance for UMAP. Smaller means tighter clusters,
                defaults to 0

            umapMetric: string or function
                Distance metric for UMAP. defaults to euclidean distance

            random_state: int
                random state
    """
    def __init__(self, nclust,
                 umapdim = 2,
                 umapN = 10,
                 umapMd = float(0),
                 umapMetric = 'euclidean',
                 random_state = 0
                 ):
        self.nclust = nclust
        self.manifoldInEmbedding = umap.UMAP(
            random_state = random_state,
            metric = umapMetric,
            n_components = umapdim,
            n_neighbors = umapN,
            min_dist = umapMd
        )

        self.clusterManifold = mixture.GaussianMixture(
            covariance_type = 'full',
            n_components = nclust, random_state = random_state
        )
        self.hle = None

    def fit(self, hl):
        self.hle = self.manifoldInEmbedding.fit_transform(hl)
        self.clusterManifold.fit(self.hle)

    def predict(self, hl):
        manifold = self.manifoldInEmbedding.transform(hl)
        y_prob = self.clusterManifold.predict_proba(manifold)
        y_pred = y_prob.argmax(1)
        return(np.asarray(y_pred))

    def fit_predict(self, hl):
        self.hle = self.manifoldInEmbedding.fit_transform(hl)
        self.clusterManifold.fit(self.hle)
        y_prob = self.clusterManifold.predict_proba(self.hle)
        y_pred = y_prob.argmax(1)
        return(np.asarray(y_pred))






def best_cluster_fit(y_true, y_pred):
    y_true = y_true.astype(np.int64)
    D = max(y_pred.max(), y_true.max()) + 1
    w = np.zeros((D, D), dtype=np.int64)
    for i in range(y_pred.size):
        w[y_pred[i], y_true[i]] += 1

    ind = la.linear_assignment(w.max() - w)
    best_fit = []
    for i in range(y_pred.size):
        for j in range(len(ind)):
            if ind[j][0] == y_pred[i]:
                best_fit.append(ind[j][1])
    return best_fit, ind, w

def cluster_acc(y_true, y_pred):
    _, ind, w = best_cluster_fit(y_true, y_pred)
    return sum([w[i, j] for i, j in ind]) * 1.0 / y_pred.size

def plot(x, y, plot_id, names=None, n_clusters = 10):
    viz_df = pd.DataFrame(data=x[:5000])
    viz_df['Label'] = y[:5000]
    if names is not None:
        viz_df['Label'] = viz_df['Label'].map(names)
    plt.subplots(figsize=(8, 5))
    sns.scatterplot(x=0, y=1, hue='Label', legend='full', hue_order=sorted(viz_df['Label'].unique()), palette=sns.color_palette("hls", n_colors=n_clusters),
                    alpha=.5,
                    data=viz_df)
    l = plt.legend(bbox_to_anchor=(-.1, 1.00, 1.1, .5), loc="lower left", markerfirst=True,
                   mode="expand", borderaxespad=0, ncol=n_clusters + 1, handletextpad=0.01, )

    # l = plt.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)
    l.texts[0].set_text("")
    plt.ylabel("")
    plt.xlabel("")
    plt.tight_layout()
    plt.title(plot_id, pad = 50)

class n2d:
    """
        n2d: Class for n2d

        Parameters:
        ------------

        input_dim: int
             dimensions of input

        manifoldLearner: initialized class, such as UmapGMM
            the manifold learner and clustering algorithm. Class should have at
            least fit and predict methods. Needs to be initialized

        autoencoder: class
            class of the autoencoder. Defaults to standard AutoEncoder class.
            Class must have a fit method, and be structured similar to the example
            on read the docs. At the very least, the embedding must be accessible
            by name (encoder_%d % middle layer index)

        architecture: list
            hidden architecture of the autoencoder. Defaults to [500,500,2000],
            meaning that the encoder is [inputdim, 500, 500, 2000, ndim], and
            the decoder is [ndim, 2000, 500, 500, inputdim].

        ae_dim: int
            number of dimensions you wish the autoencoded embedding to be.
            Defaults to 10. It is reasonable to set this to the number of clusters

        ae_args: dict
            dictionary of arguments for the autoencoder. Defaults to just
            setting the activation function to relu
    """
    def __init__(self,input_dim,
                 manifoldLearner,
                 autoencoder = AutoEncoder,
                 architecture = [500,500,2000],
                 ae_dim = 10,
                 ae_args = {"act":"relu"},
                 ):

        # FIGURE THIS OUT!! WHERE DOES X GO??


        self.autoencoder = autoencoder(input_dim = input_dim,
                                       output_dim = ae_dim,
                                       architecture = architecture,
                                       **ae_args)
        self.manifoldLearner = manifoldLearner
        self.encoder = self.autoencoder.encoder
        self.ndim = ndim
        self.preds = None
        self.hle = None



    def fit(self,x,batch_size = 256, pretrain_epochs = 1000,
                     loss = 'mse', optimizer = 'adam',weights = None,
                     verbose = 1, weight_id = 'generic_autoencoder',
            patience = None):

        """fit: train the autoencoder.

            Parameters:
            -----------------
            x: array-like
            the input data

            batch_size: int
            the batch size

            pretrain_epochs: int
            number of epochs you wish to run.

            loss: string or function
            loss function. Defaults to mse

            optimizer: string or function
            optimizer. defaults to adam

            weights: string
            if weights is used, the path to the pretrained nn weights.

            verbose: int
            how verbose you wish the autoencoder to be while training.

            weight_id: string
            where you wish to save the weights

            patience: int or None
            if patience is None, do nothing special, otherwise patience is the
            early stopping criteria


            """


        self.autoencoder.fit(x = x,
                                  batch_size = batch_size,
                                  pretrain_epochs = pretrain_epochs,
                                  loss = loss,
                                  optimizer =optimizer, weights = weights,
                                  verbose = verbose, weight_id = weight_id, patience = patience)
        hl = self.encoder.predict(x)
        self.manifoldLearner.fit(hl)


    def predict(self, x):
        hl = self.encoder.predict(x)
        self.preds = self.manifoldLearner.predict(hl)
        self.hle = self.manifoldLearner.hle
        return(self.preds)

    def fit_predict(self,x,batch_size = 256, pretrain_epochs = 1000,
                     loss = 'mse', optimizer = 'adam',weights = None,
                     verbose = 1, weight_id = 'generic_autoencoder',
            patience = None):

        self.autoencoder.fit(x = x,
                                  batch_size = batch_size,
                                  pretrain_epochs = pretrain_epochs,
                                  loss = loss,
                                  optimizer =optimizer, weights = weights,
                                  verbose = verbose, weight_id = weight_id, patience = patience)
        hl = self.encoder.predict(x)
        self.preds = self.manifoldLearner.fit_predict(hl)
        self.hle = self.manifoldLearner.hle
        return(self.preds)

    def assess(self, y):
        y = np.asarray(y)
        acc = np.round(cluster_acc(y, self.preds), 5)
        nmi = np.round(metrics.normalized_mutual_info_score(y, self.preds), 5)
        ari = np.round(metrics.adjusted_rand_score(y, self.preds), 5)

        return(acc, nmi, ari)


    def visualize(self, y, names,  nclust = 10):
        """
            visualize: visualize the embedding and clusters

            Parameters:
            -----------

            y: true clusters/labels, if they exist. Numeric
            names: the names of the clusters, if they exist
            savePath: path to save figures
            nclust: number of clusters.
        """
        y = np.asarray(y)
        y_pred = np.asarray(self.preds)
        hle = self.hle
        plot(hle, y, 'n2d', names,  n_clusters = nclust)
        y_pred_viz, _, _ = best_cluster_fit(y, y_pred)
        plot(hle, y_pred_viz, 'n2d-predicted', names,  n_clusters = nclust)
