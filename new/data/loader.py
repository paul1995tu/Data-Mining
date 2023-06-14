import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Set
import os
from omegaconf import OmegaConf
from multiprocessing import Pool
from pandarallel import pandarallel
import torch

### IMPORTANT: Assume that all files are interpolated!"
class DataLoader:

    def __init__(self, config_path="remake/config/data.yaml") -> None:
        """
        The init function of the data loader.

        Parameters:
        -----------
        config_path : str
            The path to the config file.

        Returns:
        --------
        None
        """
        pandarallel.initialize()
        if os.path.exists(config_path):
            self.config = OmegaConf.load(config_path)
            if os.path.exists(self.config["hyperparameter"]):
                self.hyperparameter_csv = pd.read_csv(self.config["hyperparameter"])
            else:
                raise FileNotFoundError("The hyperparameter file does not exist.")
        else:
            raise FileNotFoundError("The config file does not exist.")
        DATA_DIR = self.config["data_dir"]

  
    def get_strategies(self) -> List[str]:
        """
        Function to get all strategies descriped in the config file.

        Parameters:
        -----------
        None

        Returns:
        --------
        strategies : List[str]
            The list of all strategies.
        """
        return self.config["strategies"]

    def get_metrices(self) -> List[str]:
        """
        Function to get all metrices descriped in the config file.

        Parameters:
        -----------
        None

        Returns:
        --------
        metrices : List[str]
            The list of all metrices.
        """
        return self.config["metrices"]

    def get_datasets(self) -> List[str]:
        """
        Function to get all datasets descriped in the config file.

        Parameters:
        -----------
        None

        Returns:
        --------
        datasets : List[str]
            The list of all datasets.
        """
        return self.config["datasets"]

    def load_files_per_metric_and_dataset(self, metric: str, dataset: str) -> List[Tuple[str, pd.DataFrame]]:
        """
        Function to read in dataframes in parallel, given a metric and a dataset.

        Parameters:
        -----------
        metric : str
            The metric to load.
        dataset : str
            The dataset to load.
        
        Returns:
        --------
        results : List[Tuple[str, pd.DataFrame]]
            The list of tuples consisting of the strategy name and the corresponding data frame.
        """
        all_files: List[str] = [
            "kp_test_int/strategies/" + strat + "/" + dataset + "/" + metric
            for strat in self.config["strategies"]
        ]
        with Pool() as pool:
            results = pool.map(self.read_file, all_files)
        results = sorted(list(results), key=lambda x: x[0])
        return results

    def read_file(self, path: str) -> Tuple[str, pd.DataFrame]:
        """
        Function to return a single file and the name of the corresponding strategy.

        Paramters:
        ----------
        path : str
            The path of the strategie.

        Returns:
        --------
        name, csv_file : Tuple[str, pd.DataFrame]
            The tuple consisting of a string and a data frame.
        """
        df = pd.merge(pd.read_csv(path), self.hyperparameter_csv, on="EXP_UNIQUE_ID")
        df = df.sort_values(by=[
                "EXP_START_POINT",
                "EXP_BATCH_SIZE",
                "EXP_LEARNER_MODEL",
                "EXP_TRAIN_TEST_BUCKET_SIZE",
            ], ascending=[True, True, True, True])
        df = df.iloc[:, :50]
        return tuple([path.split("/")[2], df])

    
    def get_hyperparamter_csv(self) -> pd.DataFrame:
        """
        Function to return the hyperparameter csv.

        Paramters:
        ----------
        None

        Returns:
        --------
        hyperparameter_csv : pd.DataFrame
            The hyperparameter csv.            
        """
        return self.hyperparameter_csv

    def get_hyperparamter_tuples(self) -> Set[Tuple[int, int, int, int]]:
        """
        Function to return the hyperparameter tuples.

        Paramters:
        ----------
        None

        Returns:
        --------
        hyperparameter_tuples : Set[Tuple[int, int, int, int]]
            The set of hyperparameter tuples.
        """
        frame: pd.DataFrame = self.get_hyperparamter_csv().copy()
        # locate important columns in the frame
        frame = frame[
            [
                "EXP_START_POINT",
                "EXP_BATCH_SIZE",
                "EXP_LEARNER_MODEL",
                "EXP_TRAIN_TEST_BUCKET_SIZE",
            ]
        ]
        return set(frame.parallel_apply(tuple, axis=1))
    
    def retrieve_tensor(self, metric:str, dataset:str) -> Tuple[List[str], torch.Tensor] | None:
        """
        Converts the list of dataframes into a tensor.

        Parameters:
        -----------
        metric : str
            The metric to load.
        dataset : str
            The dataset to load.

        Returns:
        --------
        names : List[str]
            The list of strategy names.
        tensor : torch.Tensor
            The tensor containing the data.
        """
        data:List[Tuple[str, pd.DataFrame]] = self.load_files_per_metric_and_dataset(metric, dataset)
        names:List[str] = [x[0] for x in data]
        data:List[np.ndarray] = [x[1].to_numpy() for x in data]
        try:
            assert all([x.shape == data[0].shape for x in data])
        except AssertionError:
            print("The dataframes do not have the same shape. No clustering!")
            return None
        return names, torch.tensor(data, dtype=torch.float32)
