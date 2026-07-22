#---------------------------------------------------------------------------------
# Clean dataset
#---------------------------------------------------------------------------------

# Import libraries
from pathlib import Path
import pandas as pd

def piezometer_dataset_cleaning(file):
    """
    Objectives of this function is to clean the piezometer dataset before merging with 
    weather dataset and EDA.
    """
    # Import of the dataset
    base_dir = Path(__file__).resolve().parents[2]
    input_path = base_dir / 'data' / 'external' / file
    df = pd.read_csv(input_path)
    
    # Dropping columns
    df["date_mesure"] = pd.to_datetime(df["date_mesure"])
    columns_to_drop = ['code_nature_mesure', 'nom_nature_mesure', 'Unnamed: 0', 'urn_bss', 
                       'timestamp_mesure', 'statut', 'qualification', 'code_continuite', 
                       'nom_continuite', 'code_producteur', 'profondeur_nappe']
    df_drop = df.drop(columns=columns_to_drop)
    
    # Changing the name of the column date (preparation for future merging)
    df_drop = df_drop.rename(columns={'date_mesure': 'date_index'})
    
    # Saving the dataset after cleaning
    output_path = base_dir / 'data' / 'interim' / 'piezometer_cleaned.csv'
    df_drop.to_csv(output_path, index=False)

piezometer_dataset_cleaning(file='piezometre_data.csv')