from src.modeling.classifiers import NoFomoXGBoost, NoFomoLogRegression, NoFomoRandomForest
from src.modeling.data_pipeline import DataPipeline
model = NoFomoRandomForest(name='model_search', load=True)
pipeline = DataPipeline()

def predict_from_url(url):
    data_point = pipeline.data_point_from_url(url)
    #prediction = model.predict_single(data_point)
    prediction = model.predict_proba_single(data_point)

    return prediction, \
           data_point['performers'], \
           data_point['venue'], \
           data_point['city'], \
           data_point['country'], \
           data_point['event_url']