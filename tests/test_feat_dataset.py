# tests/test_build_features.py

import pandas as pd
from unittest.mock import patch, MagicMock

from src.data.feat_dataset import feat_dataset


@patch("src.data.feat_dataset.feature_engineering")
@patch("src.data.feat_dataset.read_csv_in_s3")
@patch("src.data.feat_dataset.boto3.client")
def test_feat_dataset_pipeline(mock_boto, mock_read, mock_fe):
    df_interim   = pd.DataFrame({"date_index": ["2023-01-01"], "code_bss": ["A"]})
    df_processed = pd.DataFrame({"feature_1": [0.5]})

    mock_boto.return_value = MagicMock()          # s3 client fictif
    mock_read.return_value = df_interim
    mock_fe.return_value   = df_processed

    result = feat_dataset(save_csv=False)

    mock_read.assert_called_once()
    mock_fe.assert_called_once_with(df_interim, save_file=False)
    assert result.equals(df_processed)