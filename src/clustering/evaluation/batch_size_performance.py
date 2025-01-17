import sys
from typing import List, Dict

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt


class BatchSizePerformance:

    def __init__(self, source_directory: str, destination_directory: str):
        self.wanted_metrics = ['accuracy', 'weighted_f1-score', 'weighted_precision', 'weighted_recall']
        self.source = source_directory
        self.destination = destination_directory

        self.hyperparameters = pd.read_csv(f"{self.source}/05_done_workload.csv")

    @staticmethod
    def get_subdirectories(path: str) -> List[str]:
        return sorted([entry.name for entry in os.scandir(path) if entry.is_dir() and not entry.name.startswith('_')])

    def get_all_strategies(self):
        return self.get_subdirectories(self.source)

    def generate_plot_for(self, dataset: str, metric: str):
        categorized = {}
        for batch_size in [1, 5, 10]:
            categorized[batch_size] = []

        # Calculate average slope for a given dataset and metric
        for strategy in self.get_all_strategies():
            path_to_metric = f'{self.source}/{strategy}/{dataset}/{metric}.csv.xz'

            # Load dataframe
            try:
                df = pd.merge(pd.read_csv(path_to_metric), self.hyperparameters, on="EXP_UNIQUE_ID")
                for batch_size in [1, 5, 10]:
                    dummy: pd.DataFrame = df.loc[df["EXP_BATCH_SIZE"] == batch_size].iloc[:, :-9]
                    # dummy.to_csv(f'{self.destination}/{metric}_{strategy}_{batch_size}.csv', index=False)
                    time_series = dummy.to_numpy().tolist()
                    time_series = time_series if time_series is not None else []
                    for series in time_series:
                        categorized[batch_size].append(series)
            except FileNotFoundError:
                pass

        to_plot = []
        legend = []
        for key in [1, 5, 10]:
            # Calculate average time series
            time_series = categorized[key]
            to_plot.append([sum(elements) / len(time_series) for elements in zip(*time_series)])
            legend.append(f'Batch size: {key}')

        # Plot the time series
        for series in to_plot:
            plt.plot(series)
        plt.xlabel('Score')
        plt.xlabel('Iteration')
        plt.title(f'Average time series for dataset \'{dataset}\' and metric \'{metric}\'')
        plt.legend(legend)
        plt.savefig(f'{self.destination}/{dataset}_{metric}.svg', format='svg')
        plt.clf()

    # Generate a plot for each dataset and metric in 'self.wanted_metrics'
    def generate_all_plots_for_dataset(self, index: int):
        if index <= len(self.get_all_datasets()):
            dataset = self.get_all_datasets()[index]
            for metric in self.wanted_metrics:
                self.generate_plot_for(dataset=dataset, metric=metric)

    def generate_all_plots_for_metric(self, index: int):
        if index <= len(self.wanted_metrics):
            metric = self.wanted_metrics[index]
            self.generate_all_average(metric=metric)

    def get_all_datasets(self):
        datasets = []
        for strategy in self.get_all_strategies():
            path_to_datasets = f"{self.source}/{strategy}"
            datasets.extend(self.get_subdirectories(path_to_datasets))
        return sorted(list(set(datasets)))

    def generate_all_average(self, metric: str):
        categorized = {}
        for batch_size in [1, 5, 10]:
            categorized[batch_size] = []

        # Calculate average slope for a given metric
        for dataset in self.get_all_datasets():
            for strategy in self.get_all_strategies():
                path_to_metric = f'{self.source}/{strategy}/{dataset}/{metric}.csv.xz'

                # Load dataframe
                try:
                    df = pd.merge(pd.read_csv(path_to_metric), self.hyperparameters, on="EXP_UNIQUE_ID")
                    for batch_size in [1, 5, 10]:
                        dummy: pd.DataFrame = df.loc[df["EXP_BATCH_SIZE"] == batch_size].iloc[:, :-9]
                        # dummy.to_csv(f'{self.destination}/{metric}_{strategy}_{batch_size}.csv', index=False)
                        time_series = dummy.to_numpy().tolist()
                        time_series = time_series if time_series is not None else []
                        for series in time_series:
                            categorized[batch_size].append(series)
                except FileNotFoundError:
                    pass

        to_plot = []
        legend = []
        for key in [1, 5, 10]:
            # Calculate average time series
            time_series = categorized[key]
            to_plot.append([sum(elements) / len(time_series) for elements in zip(*time_series)])
            legend.append(f'Batch size: {key}')

        # Plot the time series
        for series in to_plot:
            plt.plot(series)
        plt.xlabel('Score')
        plt.xlabel('Iteration')
        plt.title(f'Average time series for metric \'{metric}\'')
        plt.legend(legend)
        plt.savefig(f'{self.destination}/{metric}.svg', format='svg')
        plt.clf()


hpc: bool = False

if hpc:
    source = '/home/vime121c/Workspaces/scratch/vime121c-db-project/Extrapolation'
    destination = '/home/vime121c/Workspaces/scratch/vime121c-db-project/generated/Plots'

    if len(sys.argv) > 1:
        index = int(sys.argv[1])
        analysis = BatchSizePerformance(source_directory=source, destination_directory=destination)
        analysis.generate_all_plots_for_dataset(index=index)
        analysis.generate_all_plots_for_metric(index=index)

else:
    source = '/home/ature/University/6th-Semester/Data-Mining/kp_test/strategies'
    destination = '/home/ature/Programming/Python/DB-Mining-Data/Plots'

    analysis = BatchSizePerformance(source_directory=source, destination_directory=destination)
    analysis.generate_plot_for(dataset='Iris', metric='accuracy')
    analysis.generate_all_average(metric='accuracy')
