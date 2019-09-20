from src.modeling.classifiers import RandomForest
from src.modeling.data_pipeline import DataPipeline
model = RandomForest(init_as='random_forest_19-09-2019')
pipeline = DataPipeline()

def predict_from_url(url):
    data_point = pipeline.data_point_from_url(url)
    prediction = model.predict(data_point)
    return prediction, \
           data_point['performers'], \
           data_point['venue'], \
           data_point['city'], \
           data_point['country'], \
           data_point['event_url']