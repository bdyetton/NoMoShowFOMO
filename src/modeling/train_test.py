import pandas as pd
from src.modeling import visualization, classifiers, calc_features
from sklearn.model_selection import train_test_split
import numpy as np

def split_to_train_test(clean_data, DV, IVs, test_size=0.3):
    sold_out = clean_data.loc[clean_data[DV]=='sold_out',:]
    avail = clean_data.loc[clean_data[DV]!='sold_out',:]
    n_soldout = sold_out.shape[0]
    avail = avail.sample(n=n_soldout)
    clean_data = pd.concat([sold_out, avail])
    X=clean_data[IVs]
    y=clean_data[DV]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=0)
    print('Length of train set: \t %f' % len(X_train))
    print('Length of test set: \t %f\n' % len(X_test))
    y_train = y_train.ravel()
    y_test = y_test.ravel()
    return X_train, X_test, y_train, y_test


def vis_data(data, DV, cat_IVs, cont_IVs):
    IVs = cat_IVs + cont_IVs
    visualization.report_nans(IVs, data)
    visualization.plot_DV_counts(DV, data)
    visualization.plot_week_day_effect(DV, data)
    visualization.pairplot(cont_IVs, data)
    visualization.correl_heatmap(data[IVs])


def fit_model(model, data):
    print(data.shape)
    X_train, X_test, y_train, y_test = split_to_train_test(data, model.DV, model.IVs)
    model.fit(X_train, y_train)
    model.score(X_test, y_test)
    model.performance(X_test, y_test)
    if hasattr(model, 'feature_importance'):
        model.feature_importance()
    model.save()

if __name__ == '__main__':
    data = pd.read_pickle('../../data/combined_19-09-2019.pkl')
    sk = pd.read_pickle('../../data/songkick_temp19-09-2019.pkl').set_index('idx')
    data = data.drop([col for col in sk.columns if col in data.columns], axis=1)
    pop = pd.read_pickle('../../data/trends_19-09-2019.pkl')
    data = pd.merge(sk, data, left_index=True, right_index=True)
    data = pd.merge(pop, data, left_index=True, right_index=True)

    DV = 'avail_mode'
    cont_IVs = ['sk_popularity', 'days_since_last_played', 'total_times_played_locally', 'popularity_in_country_resid',
                'popularity_in_region', 'days_on_sale', 'venue_capacity', 'population', 'time_of_day',
                'days_to_event']
    cat_IVs = ['weekend_event', 'mid_week_event']
    IVs = cont_IVs+cat_IVs

    data.loc[data[DV] == 'limited', DV] = 'none'
    data.loc[data[DV] == 'none', DV] = 'sold_out'
    data = data.fillna(np.nan)
    data = calc_features.features_for_dataset(data)
    data = calc_features.fill_na(data)
    #vis_data(data, DV, cat_IVs, cont_IVs)
    data = data[IVs+[DV]].dropna()
    model = classifiers.NoFomoXGBoost('testing', IVs=IVs, DV=DV, hyper_params={'n_estimators':50})
    fit_model(model, data)