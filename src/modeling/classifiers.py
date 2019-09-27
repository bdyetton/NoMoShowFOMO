import pickle
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier, plot_importance
from sklearn.model_selection import RandomizedSearchCV, KFold
import os
import shap
from scipy import stats
import numpy as np
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
my_dir = os.path.dirname(__file__) + '/'


class MyLogSpace():
    def __init__(self,a,b):
        self.a = a
        self.b = b

    def rvs(self, random_state=None):
        return 10 ** np.random.uniform(self.a, self.b)

class BaseClassifier():
    def __init__(self, name, IVs, DV, model):
        self.IVs = IVs
        self.DV = DV
        self.model = model
        self.name = name
        self.param_dist = None

    def fit(self, data):
        self.model.fit(data[self.IVs], data[self.DV].values.ravel())

    def predict_single(self, data_point):
        return self.model.predict(data_point[self.IVs].values.reshape(1, -1))[0] == 'sold_out'

    def score(self, data):
        acc = self.model.score(data[self.IVs], data[self.DV].values.ravel())
        print('Accuracy: %f\n' % acc)
        return acc

    def performance(self, data):
        y_pred = self.model.predict(data[self.IVs])
        # classification report
        y = data[self.DV].values.ravel()
        print(classification_report(y, y_pred))

        # confusion matrix
        print('Confusion Matrix\n')
        cm = confusion_matrix(y, y_pred)
        print(cm)

    def save(self):
        pickle.dump((self.model, self.IVs, self.DV), open(my_dir+'../../models/'+self.name+'.pkl','wb'))

    def fit_cv(self, data):
        cv_search = RandomizedSearchCV(self.model, param_distributions=self.param_dist, n_iter=25, scoring='f1', error_score=0, verbose=3,
                             n_jobs=-1, cv=5, return_train_score=True)
        X = data[self.IVs]
        y = data[self.DV]
        cv_search.fit(X, y)
        print('mean_test_score', cv_search.cv_results_['mean_test_score'][cv_search.best_index_])
        self.model = cv_search.best_estimator_
        return cv_search.cv_results_['mean_train_score'][cv_search.best_index_], \
               cv_search.cv_results_['mean_test_score'][cv_search.best_index_]


class NoFomoRandomForest(BaseClassifier):
    def __init__(self, name=None, load=False, IVs=None, DV=None, hyper_params={}):
        name = 'random_forest_'+name
        if load:
            self.model, self.IVs, self.DV = pickle.load(open(my_dir+'../../models/'+name+'.pkl','rb'))
        else:
            model = RandomForestClassifier(**hyper_params)
            super(NoFomoRandomForest, self).__init__(name, IVs, DV, model)

        self.param_dist = {'bootstrap': [True, False],
                           'max_depth': stats.randint(3,9),
                           'max_features': ['auto', 'sqrt'],
                           'min_samples_leaf': [1, 2, 4],
                           'min_samples_split': [2, 5, 10],
                           'n_estimators': stats.randint(150,500)}

    def interpret_features(self):
        coef = self.model.feature_importances_
        plt.barh(range(len(self.IVs)), coef, align='center')
        plt.yticks(range(len(self.IVs)), self.IVs)
        plt.show()

class NoFomoLogRegression(BaseClassifier):
    def __init__(self, name=None, load=False, IVs=None, DV=None, hyper_params={}):
        name = 'log_reg_' + name
        if load:
            self.model, self.IVs, self.DV = pickle.load(open(my_dir + '../../models/' + name + '.pkl', 'rb'))
        else:
            model = LogisticRegression(**hyper_params)
            super(NoFomoLogRegression, self).__init__(name, IVs, DV, model)

        self.param_dist = {'penalty':['l1', 'l2'],
                           'C': MyLogSpace(-3,3)}

    def interpret_features(self):
        coef = self.model.coef_
        plt.barh(range(len(self.IVs)), coef[0], align='center')
        plt.yticks(range(len(self.IVs)), self.IVs)
        plt.show(block=True)


class NoFomoXGBoost(BaseClassifier):
    def __init__(self, name=None, load=False, IVs=None, DV=None, hyper_params={}):
        name = 'xgb_'+name
        if load:
            self.model, self.IVs, self.DV = pickle.load(open(my_dir+'../../models/'+name+'.pkl','rb'))
        else:
            model = XGBClassifier(**hyper_params)
            super(NoFomoXGBoost, self).__init__(name, IVs, DV, model)

        self.param_dist = {
            'n_estimators': stats.randint(150, 500),
            'learning_rate': stats.uniform(0.01, 0.07),
            'subsample': stats.uniform(0.3, 0.7),
            'max_depth': [3, 4, 5, 6, 7, 8, 9],
            'colsample_bytree': stats.uniform(0.5, 0.45),
            'min_child_weight': [1, 2, 3],
            'alpha': MyLogSpace(-3, 2)
                           }

    def interpret_features(self):
        #plot_importance(self.model, importance_type='gain')
        #plt.show()
        plot_importance(self.model, importance_type='weight', show_values=False)
        plt.show()
        #plot_importance(self.model, importance_type='cover')
        #plt.show()

    def shap_explain(self, data):
        shap_values = shap.TreeExplainer(self.model).shap_values(data[self.IVs])
        shap.summary_plot(shap_values, data[self.IVs])
        #plt.gcf().subplots_adjust(left=1)
        plt.show()