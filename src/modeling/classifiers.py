import pickle
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
import os
my_dir = os.path.dirname(__file__) + '/'

class BaseClassifier():
    def __init__(self, name, IVs, DV, model):
        self.IVs = IVs
        self.DV = DV
        self.model = model
        self.name = name

    def fit(self, X, Y):
        self.model.fit(X, Y)

    def predict_single(self, data_point):
        return self.model.predict(data_point[self.IVs].values.reshape(1, -1))[0] == 'sold_out'

    def score(self, X, y):
        acc = self.model.score(X[self.IVs], y)
        print('Accuracy: %f\n' % acc)
        return acc

    def performance(self, X, y):
        y_pred = self.model.predict(X[self.IVs])
        # classification report
        print(classification_report(y, y_pred))

        # confusion matrix
        print('Confusion Matrix\n')
        cm = confusion_matrix(y, y_pred)
        print(cm)

    def save(self):
        pickle.dump((self.model, self.IVs, self.DV), open(my_dir+'../../models/'+self.name+'.pkl','wb'))


class NoFomoRandomForest(BaseClassifier):
    def __init__(self, name=None, load=False, IVs=None, DV=None, hyper_params={}):
        name = 'random_forest_'+name
        if load:
            self.model, self.IVs, self.DV = pickle.load(open(my_dir+'../../models/'+name+'.pkl','rb'))
        else:
            model = RandomForestClassifier(**hyper_params)
            super(NoFomoRandomForest, self).__init__(name, IVs, DV, model)

    def interpret_features(self):
        coef = self.model.feature_importances_
        plt.barh(range(len(self.IVs)), coef, align='center')
        plt.yticks(range(len(self.IVs)), self.IVs)
        plt.show()

class NoFomoXGBoost(BaseClassifier):
    def __init__(self, name=None, load=False, IVs=None, DV=None, hyper_params={}):
        name = 'xgb_'+name
        if load:
            self.model, self.IVs, self.DV = pickle.load(open(my_dir+'../../models/'+name+'.pkl','rb'))
        else:
            model = XGBClassifier(**hyper_params)
            super(NoFomoXGBoost, self).__init__(name, IVs, DV, model)

    def interpret_features(self):
        coef = self.model.feature_importances_
        plt.barh(range(len(self.IVs)), coef, align='center')
        plt.yticks(range(len(self.IVs)), self.IVs)
        plt.show()