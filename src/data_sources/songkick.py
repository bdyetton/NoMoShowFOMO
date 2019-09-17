import json
import os
import requests
import numpy as np
import pandas as pd
import datetime
import mpu
import time
from fuzzywuzzy import fuzz
import pytz

def point_dist(x1,y1,x2,y2):
    return np.sqrt((x1-x2)**2 + (y1-y2)**2)

class SongKick():
    def __init__(self):
        #self.tzwhere = tzwhere.tzwhere()
        self.base = 'https://api.songkick.com/api/3.0/search/'
        self.api_key = os.getenv('songkick_api_key')
        self.default_params = '&apikey='+self.api_key #&domain=canada
        self.req = requests.session()

    def get_venue_capacity(self, venue_name, expected_lat, expected_long):
        _, metro_area, _ = self.get_songkick_city_and_metro_region(expected_lat, expected_long)
        if pd.isna(metro_area):
            query = venue_name
        else:
            query = venue_name + ' ' + metro_area
        venues_info = json.loads(self.req.get(self.base + 'venues.json?query='+query+self.default_params).content)
        if venues_info['resultsPage']['status'] == 'ok' and len(venues_info['resultsPage']['results'])>0:
            venues = venues_info['resultsPage']['results']['venue']
            venue_cont = []
            for venue in venues:
                if venue['capacity'] is None:
                    continue
                row = {}
                row['venue_capacity'] = venue['capacity']
                row['venue_name'] = venue['displayName']
                row['venue_fuzzwuzz_score'] = fuzz.token_set_ratio(venue_name, row['venue_name'])
                row['venue_city'] = venue['city']['displayName']
                row['venue_country'] = venue['city']['country']['displayName']
                if venue['lat'] and venue['lng']:
                    row['venue_lat'] = venue['lat']
                    row['venue_long'] = venue['lng']
                    row['venue_dist_from_expected'] = mpu.haversine_distance((venue['lat'], venue['lng']), (expected_lat, expected_long))
                else:
                    continue
                venue_cont.append(pd.Series(row))
            if len(venue_cont) == 0:
                return pd.Series()
            venue_df = pd.concat(venue_cont, axis=1).T
            possible_matches = venue_df.loc[venue_df['venue_dist_from_expected']<10,:] #should be less than 1 km from expected loc
            if possible_matches.shape[0] > 0:
                return possible_matches.sort_values('venue_fuzzwuzz_score', ascending=False).iloc[0]
            else:
                return pd.Series()
        else:
            return pd.Series()

    def get_songkick_popularity(self, artist, event_date, lat, long):
        event_data = json.loads(self.req.get('https://api.songkick.com/api/3.0/events.json?'
                                           + '&location=geo:'+str(lat)+','+str(long)
                                           + '&artist_name='+artist
                                           + '&min_date='+event_date.strftime('%Y-%m-%d')
                                           + '&max_date='+event_date.strftime('%Y-%m-%d')
                                           + self.default_params).content)
        if event_data['resultsPage']['status'] != 'ok':
            return np.nan
        else:
            if len(event_data['resultsPage']['results']) > 0:
                return event_data['resultsPage']['results']['event'][0]['popularity']
            else:
                return np.nan


    def get_songkick_city_and_metro_region(self, lat, long):
        loc_data = json.loads(self.req.get(self.base + 'locations.json?location=geo:'
                                              +str(lat)+','+str(long)
                                              +self.default_params).content)
        if loc_data['resultsPage']['status'] != 'ok':
            return np.nan, np.nan, np.nan
        else:
            return loc_data['resultsPage']['results']['location'][0]['city']['displayName'], \
                    loc_data['resultsPage']['results']['location'][0]['metroArea']['displayName'], \
                      loc_data['resultsPage']['results']['location'][0]['metroArea']['id']


    def get_last_local_events(self, artist, event_date, lat, long):
        artist_info = json.loads(self.req.get(self.base + 'artists.json?query='+artist
                                              +self.default_params).content)
        row = {}
        if artist_info['resultsPage']['status'] != 'ok':
            return pd.DataFrame()
        if len(artist_info['resultsPage']['results']) == 0:
            return pd.DataFrame()
        row['artist_id'] = artist_info['resultsPage']['results']['artist'][0]['id'] #TODO check if best match is always 0
        row['artist_name'] = artist_info['resultsPage']['results']['artist'][0]['displayName']
        url = 'https://api.songkick.com/api/3.0/artists/'+str(row['artist_id'])+'/gigography.json?'
        try:
            gigography = json.loads(self.req.get(url+self.default_params).content) #TODO do retries
        except json.decoder.JSONDecodeError:
            try:
                time.sleep(1)
                gigography = json.loads(self.req.get(url + self.default_params).content)
            except json.decoder.JSONDecodeError:
                return pd.DataFrame()
        if gigography['resultsPage']['status'] != 'ok':
            return pd.DataFrame()
        events = []
        events += gigography['resultsPage']['results']['event']
        page = gigography['resultsPage']['page']
        total_events = gigography['resultsPage']['totalEntries']
        current_idx = gigography['resultsPage']['page']*gigography['resultsPage']['perPage']
        while current_idx < total_events:
            gigography = json.loads(self.req.get(url + 'page='+str(page+1) + self.default_params).content)
            if gigography['resultsPage']['status'] != 'ok':
                break
            events += gigography['resultsPage']['results']['event']
            page = gigography['resultsPage']['page']
            total_events = gigography['resultsPage']['totalEntries']
            current_idx = gigography['resultsPage']['page'] * gigography['resultsPage']['perPage']

        last_local_events_cont = []
        for event in events:
            event_start = datetime.datetime.fromisoformat(event['start']['date'])
            if event_date.date()<event_start.date():
                continue
            if event['location']['lat'] is None or event['location']['lng'] is None:
                continue
            dist_from_current_event = mpu.haversine_distance((event['location']['lat'], event['location']['lng']), (lat, long))
            if dist_from_current_event > 45: #less than 30 km
                continue
            row = {}
            row['venue'] = event['venue']['displayName']
            row['event_start'] = event_start
            row['lat'] = event['location']['lat']
            row['long'] = event['location']['lng']
            row['id'] = event['id']
            row['dist_from_current'] = dist_from_current_event
            last_local_events_cont.append(pd.Series(row))
        if len(last_local_events_cont) == 0:
            return pd.DataFrame()
        last_local_events = pd.concat(last_local_events_cont, axis=1).T
        last_local_events = last_local_events.sort_values('event_start', ascending=False)
        return last_local_events

if __name__=='__main__':
    sk = SongKick()
    print(sk.get_songkick_popularity('Elder Island', datetime.datetime.now(), 37.73, -122.43))
    #print(sk.get_songkick_city_and_metro_region(51.5, 0.127))
    #print(sk.get_last_local_events("deadmau5", datetime.datetime.now(), 51.5, 0.127))
    print(sk.get_venue_capacity('The Fillmore', 37.73, -122.43))