import pickle

class RandomForest():
    def __init__(self, init_as=None):
        if init_as is not None:
            self.model, self.IVs, self.DV = pickle.load(open('../models/'+init_as+'.pkl','rb'))
        else:
            self.model = None

    def predict(self, data_point):
        return self.model.predict(data_point[self.IVs].values.reshape(1, -1))[0] == 'sold_out'