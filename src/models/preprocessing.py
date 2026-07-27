# Import libraries
import pandas as pd


def preprocessing(df):
    """
    This function performed the following steps:
    1. preprocessing preparation (dropping undesire columns; splitting the target 'y' and the explicatives features 'X')
    2. Temporal split (X_train; X_test; y_train & y_test)
    At the end, this function return the different datasets to perform Machine Learning algorithms.
    """
    # Setting 'date_index' as index in the dataframe
    df = df.set_index("date_index", drop=False)
    df.index = pd.to_datetime(df.index)
    
    # Build the monthly panel
    std_cols = df.filter(regex=r"^S.*I$").columns
    df = df.filter(std_cols)
    df_monthly = df.groupby(df.index.to_period('M')).mean()
    
    # Definition of the target
    df_monthly['SPLI_1m'] = df_monthly['SPLI'].shift(-1) # SPLI from the next month
    df_monthly['SPLI_2m'] = df_monthly['SPLI'].shift(-2) # SPLI from the next two months
    df_monthly['SPLI_3m'] = df_monthly['SPLI'].shift(-3) # SPLI from the next three months
    
    # Temporal split (80/20% for the train/test sets split)
    df_train = df_monthly.iloc[:-7]
    df_test = df_monthly.iloc[-7:-4]
    
    # Split X/y     
    y_train_1m = df_train['SPLI_1m']
    y_train_2m = df_train['SPLI_2m']
    y_train_3m = df_train['SPLI_3m']
    X_train = df_train.drop(columns=['SPLI', 'SPLI_1m', 'SPLI_2m', 'SPLI_3m'])
   
    y_test_1m = df_test['SPLI_1m']
    y_test_2m = df_test['SPLI_2m']
    y_test_3m = df_test['SPLI_3m']
    X_test = df_test.drop(columns=['SPLI', 'SPLI_1m', 'SPLI_2m', 'SPLI_3m'])
    
    return X_train, y_train_1m, y_train_2m, y_train_3m, X_test, y_test_1m, y_test_2m, y_test_3m