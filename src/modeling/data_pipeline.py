import pandas as pd
import os
my_file = os.path.dirname('__file__')
import src.data_sources.songkick as songkick
import src.data_sources.google_trends as google_trends
import src.data_sources.demographics as demographics
import src.data_sources.ticketmaster as ticketmaster
import src.modeling.calc_features as calc_features
debug = False

class DataPipeline():
    def __init__(self):
        self.tm = ticketmaster.TicketMaster()
        self.sk = songkick.SongKick()
        self.demo = demographics.Demographics(city_to_city=self.tm.city_to_city_map, country_to_country=self.tm.country_to_country_map)
        self.trends = google_trends.Trends(use_proxy=False)

    def data_point_from_url(self, url):
        event = self.tm.get_event_from_url(url)
        songkick_data = self.sk.get_songkick_data_for_event(event)
        trends_data = self.trends.get_geo_trends(event['performers'], 'today 5-y', self.trends.get_iso_region(event['lat'], event['long']))
        avail_data = self.tm.add_availability_info(event)
        pop_data = self.demo.get_pop(event['city'], event['country'])
        time_data = self.tm.get_time_features_for_event(event)
        data_point = calc_features.features_for_data_point(pd.concat([event, songkick_data, trends_data, avail_data, pop_data, time_data]))
        data_point = calc_features.fill_na(data_point)
        return data_point

