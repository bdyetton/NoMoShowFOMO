from src.modeling.classifiers import NoFomoRandomForest, NoFomoXGBoost
from src.modeling.data_pipeline import DataPipeline
model = NoFomoXGBoost(name='testing', load=True)
pipeline = DataPipeline()

def predict_from_url(url):
    data_point = pipeline.data_point_from_url(url)
    prediction = model.predict_single(data_point)
    return prediction, \
           data_point['performers'], \
           data_point['venue'], \
           data_point['city'], \
           data_point['country'], \
           data_point['event_url']