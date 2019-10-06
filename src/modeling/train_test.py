import pandas as pd
from src.modeling import visualization, classifiers, calc_features
from sklearn.model_selection import train_test_split
import numpy as np
import sys
import matplotlib.pyplot as plt


def balance_classes(clean_data, IVs, DV):
    assert 'days_on_sale' not in IVs
    sold_out = clean_data.loc[clean_data[DV]==1, :]
    avail = clean_data.loc[clean_data[DV]!=1, :].sort_values('days_on_sale', ascending=False)
    n_soldout = sold_out.shape[0]
    avail = avail.iloc[:n_soldout]
    return pd.concat([sold_out, avail])


def split_to_train_test(data, test_size=0.2):
    data_train_and_val, data_test = train_test_split(data, test_size=test_size)
    print('Length of train and val set: \t %f' % data_train_and_val.shape[0])
    print('Length of test set: \t %f\n' % data_test.shape[0])
    return data_train_and_val, data_test


def vis_data(data, DV, IVs):
    visualization.report_nans(IVs, data)
    visualization.plot_DV_counts(DV, data)
    visualization.plot_week_day_effect(DV, data)
    #visualization.pairplot(cont_IVs, data)
    visualization.correl_heatmap(data[IVs])


def fit_model(model, data):
    print(data.shape)
    data = balance_classes(data, model.IVs, model.DV)
    data_train_and_val, data_test = split_to_train_test(data)
    train_accuracy, val_accuracy = model.fit_cv(data_train_and_val)
    test_accuracy = model.score(data_test)
    model.performance(data_test)
    # if hasattr(model, 'feature_importance'):
    #     model.feature_importance()
    #     plt.show()
    model.save()
    return train_accuracy, val_accuracy, test_accuracy

def optimize_feature_set():
    DV = 'avail_status'
    IV_sets = {
        'base': ['sk_popularity',
           'days_since_last_played',
           'total_times_played_locally',
           'popularity_in_country_resid',
           'popularity_in_region',
           'venue_capacity',
           'population_city',
           #'population_country',
           'price_mean',
           'gdp_country',
           'time_of_day',
           'sat_event',
           'fri_event',
           'early_week_event'],

        'base_nrom': ['sk_popularity',
                 'days_since_last_played',
                 'total_times_played_locally',
                 'popularity_in_country_resid',
                 'popularity_in_region',
                 'venue_capacity_norm',
                 'population_city',
                 # 'population_country',
                 'price_mean_normalized',
                 #'gdp_country',
                 'time_of_day',
                 'sat_event',
                 'fri_event',
                 'early_week_event'],


    }
    model_set_cont = []
    for model_name, IVs in IV_sets.items():
        basedate = '22-09-2019'
        data = pd.read_pickle('../../data/combined_' + basedate + '.pkl')
        data['avail_status'] = data['avail_some_sold_out'].map({True: 1, False: 0})
        cat_IVs = []
        cont_IVs = []
        for iv in IVs:
            if iv in ['weekend_event', 'mid_week_event']:
                cat_IVs.append(iv)
            else:
                cont_IVs.append(iv)

        data.loc[data[DV] == 'limited', DV] = 'none'
        data.loc[data[DV] == 'none', DV] = 'sold_out'  # Does nothing when  these labels not present
        data = data.fillna(np.nan)
        data = calc_features.features_for_dataset(data)
        data = calc_features.fill_na(data)
        # vis_data(data, DV, cat_IVs, cont_IVs)
        data = data[IVs + [DV] + ['days_on_sale']].dropna()
        model = classifiers.NoFomoXGBoost(model_name, IVs=IVs, DV=DV)  # , hyper_params={'objective':'binary:logistic'})
        train_acc, val_acc, test_acc = fit_model(model, data)
        model_set_cont.append(pd.Series({'name': model.name, 'train_acc':train_acc, 'val_acc': val_acc, 'test_acc': test_acc}))
    model_fit_df = pd.concat(model_set_cont, axis=1).T
    print(model_fit_df)
    model_fit_df.to_csv('../../results/Variables_Fit_' + DV + '_' + basedate + '.csv', )

def optimize_model_type():
    DV = 'avail_status'
    IVs = ['sk_popularity',
           'days_since_last_played',
           'total_times_played_locally',
           'popularity_in_country_resid',
           'popularity_in_region',
           'venue_capacity',
           'population_city',
           #'population_country',
           'price_mean',
           'gdp_country',
           'time_of_day',
           'sat_event',
           'fri_event',
           'early_week_event']

    model_set_cont = []
    for base_classifier in [classifiers.NoFomoRandomForest, classifiers.NoFomoLogRegression, classifiers.NoFomoXGBoost]:#, classifiers.AdabostedSVM]:
        basedate = '22-09-2019'
        data = pd.read_pickle('../../data/combined_' + basedate + '.pkl')
        data['avail_status'] = data['avail_some_sold_out'].map({True: 1, False: 0})
        cat_IVs = []
        cont_IVs = []
        for iv in IVs:
            if iv in ['weekend_event', 'mid_week_event']:
                cat_IVs.append(iv)
            else:
                cont_IVs.append(iv)

        data.loc[data[DV] == 'limited', DV] = 'none'
        data.loc[data[DV] == 'none', DV] = 'sold_out'  # Does nothing when  these labels not present
        data = data.fillna(np.nan)
        data = calc_features.features_for_dataset(data)
        data = calc_features.fill_na(data)
        # vis_data(data, DV, cat_IVs, cont_IVs)
        data = data[IVs + [DV] + ['days_on_sale']].dropna()
        model = base_classifier('model_search2', IVs=IVs, DV=DV)  # , hyper_params={'objective':'binary:logistic'})
        train_acc, val_acc, test_acc = fit_model(model, data)
        model_set_cont.append(pd.Series({'name': model.name, 'train_acc':train_acc, 'val_acc': val_acc, 'test_acc': test_acc}))
    model_fit_df = pd.concat(model_set_cont, axis=1).T
    print(model_fit_df)
    model_fit_df.to_csv('../../results/Models_Fit_' + DV + '_' + basedate + '.csv', )

if __name__ == '__main__':
    #optimize_model_type()
    #optimize_feature_set()
    #sys.exit()
    model = classifiers.NoFomoXGBoost(name='base', load=True) #with_week_changes
    #model.interpret_features()

    basedate = '22-09-2019'
    data = pd.read_pickle('../../data/combined_' + basedate + '.pkl')
    data['avail_status'] = data['avail_some_sold_out'].map({True: 1, False: 0})
    data = data.fillna(np.nan)
    data = calc_features.features_for_dataset(data)
    data = calc_features.fill_na(data)
    #vis_data(data, model.DV, model.IVs)

    # data = data[model.IVs + [model.DV] + ['days_on_sale']].dropna()
    # #visualization.plot_week_day_effect(model.DV, data)
    model.shap_explain(data)




