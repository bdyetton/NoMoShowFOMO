import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


def plot_week_day_effect(DV, data):
    # sns.countplot(x=DV, hue='day_of_week', data=data)
    # plt.show()

    data_per_weekday_and_type = data.groupby([DV, 'day_of_week']).count()['ticketmaster_event_id']
    data_per_weekday_and_type.name = 'count'
    data_per_weekday_and_type = data_per_weekday_and_type.reset_index()
    data_per_weekday = data_per_weekday_and_type.reset_index().groupby('day_of_week').sum().reset_index()
    data_per_weekday = data_per_weekday.rename({'count': 'total'}, axis=1)
    counts = pd.merge(data_per_weekday_and_type, data_per_weekday, on='day_of_week')
    counts['percent'] = counts['count'] / counts['total']
    sns.barplot(x='day_of_week', y='percent', data=counts.loc[counts[DV] == 'sold_out', :])
    plt.show()

def report_nans(IVs, data):
    for IV in IVs:
        print('# nans for ' + IV, 100 * sum(data[IV].isna()) / data.shape[0])

def pairplot(cont_IVs, data):
    sns.pairplot(data[cont_IVs].dropna())
    plt.tight_layout()
    plt.show()

def correl_heatmap(clean_data):
    clean_data = clean_data.apply(lambda x: pd.to_numeric(x, errors='ignore'), axis=1)
    _ = sns.heatmap(clean_data.corr(), annot=True, fmt=".2f", cmap="viridis")
    plt.show()

def plot_DV_counts(DV, data):
    sns.countplot(x=DV, data=data)
    plt.show()