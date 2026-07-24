"""
FeatureEngineer — isolé dans son propre fichier, jamais exécuté comme
script (toujours importé), pour garantir un __module__ stable :
"src.models.feature_engineering.FeatureEngineer" en toutes circonstances.

Pourquoi c'est nécessaire : `python -m src.models.train` (utilisé par le
Makefile, le Dockerfile, trigger_job.py) donne à train.py un __name__
de "__main__" — EXACTEMENT comme `python src/models/train.py` lancé
directement. Si FeatureEngineer était définie dans train.py, son
__module__ deviendrait "__main__" dans ce cas, ce qui casse
`skops_trusted_types` lors du log_model MLflow (voir train.py) : le
nom qualifié utilisé au moment de sauvegarder le modèle ne correspondrait
à rien d'important ni de stable pour le chargement ailleurs.
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Transformer sklearn custom qui crée de nouvelles colonnes à partir des
    colonnes brutes (déjà nettoyées structurellement, mais pouvant encore
    contenir des NaN -> ces NaN se propagent naturellement dans les nouvelles
    colonnes et seront traités par l'imputer du ColumnTransformer en aval).

    Placé dans le pipeline (et non dans make_dataset.py) car :
    - une future feature pourrait dépendre d'une statistique du train
      (ex: écart à la moyenne du groupe) et devrait alors être fit sur
      train uniquement ;
    - on veut que la même logique s'applique automatiquement à toute
      nouvelle donnée passée à `predict()`, sans étape manuelle séparée.
    """

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        """
        Transformer sklearn custom qui crée de nouvelles colonnes à partir des
        colonnes brutes (déjà nettoyées structurellement, mais pouvant encore
        contenir des NaN -> ces NaN se propagent naturellement dans les nouvelles
        colonnes et seront traités par l'imputer du ColumnTransformer en aval).

        Placé dans le pipeline (et non dans make_dataset.py) car :
        - une future feature pourrait dépendre d'une statistique du train
        (ex: écart à la moyenne du groupe) et devrait alors être fit sur
        train uniquement ;
        - on veut que la même logique s'applique automatiquement à toute
        nouvelle donnée passée à `predict()`, sans étape manuelle séparée.
        """

        X = X.copy()

        # le feature ingeneering ici !


        return X
