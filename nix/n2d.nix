{lib, buildPythonPackage, pythonSource, umapVar}:

    buildPythonPackage rec {
      pname = "n2d";
      version = "0.1.9";
    

      src = ./..;

      buildInputs = [
        pythonSource.h5py
        pythonSource.Keras
        pythonSource.tensorflow
        pythonSource.scipy
        pythonSource.numpy
        pythonSource.pandas
        pythonSource.seaborn
        pythonSource.matplotlib
        pythonSource.scikitlearn
        pythonSource.numba
        umapVar
      ];

    }
