#---------------------------------------------------------------------------------
# Clean dataset
#---------------------------------------------------------------------------------

# Import libraries
from pathlib import Path
import pandas as pd

def piezometer_dataset_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """
    Objectives of this function is to clean the piezometer dataset before merging with 
    weather dataset and EDA.
    """
    
    # Dropping columns
    df["date_mesure"] = pd.to_datetime(df["date_mesure"])
    columns_to_drop = ['code_nature_mesure', 'nom_nature_mesure', 'Unnamed: 0', 'urn_bss', 
                       'timestamp_mesure', 'statut', 'qualification', 'code_continuite', 
                       'nom_continuite', 'code_producteur', 'profondeur_nappe']
    df = df.drop(columns=columns_to_drop)
    
    # Changing the name of the column date (preparation for future merging)
    df = df.rename(columns={'date_mesure': 'date_index'})
    
    # Export
    return df