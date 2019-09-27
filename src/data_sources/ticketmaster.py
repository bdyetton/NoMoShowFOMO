import requests
import json
import datetime
import pandas as pd
#from tzwhere import tzwhere
import pytz
import os
import numpy as np
import pickle
from forex_python.converter import CurrencyRates
import time
my_file = os.path.abspath(os.path.dirname('__file__'))

days_of_week = ['Mon', 'Tue', 'Wed', 'Thur', 'Fri', 'Sat', 'Sun']

class TicketMaster():
    def __init__(self):
        #self.tzwhere = tzwhere.tzwhere()
        self.base = 'https://app.ticketmaster.eu/mfxapi/v2/'
        self.currency_convert_base = ''
        self.api_key = os.environ['ticketmaster_api_key']
        self.default_params = '&lang=en-en'+\
                              '&category_ids=10001' +\
                              '&is_not_package=true' +\
                              '&exlude_external=true' +\
                              '&cancelled=False'+\
                              '&rows=250'+\
                              '&apikey='+self.api_key
        self.req = requests.session()
        self.site_to_domain_map = {}
        self.city_to_city_map = {}
        self.country_to_country_map = {}
        self.forex = CurrencyRates()
        self.get_domain_maps(load=True, save=False)


    def get_domain_maps(self, load=False, save=False):
        if load:
            try:
                self.site_to_domain_map, self.city_to_city_map, self.country_to_country_map = pickle.load(open('tm_maps.pkl','rb'))
                return
            except FileNotFoundError:
                pass
        print('Building new map for cities')
        ret = json.loads(self.req.get(self.base+'domains?apikey='+self.api_key).content)
        for dom in ret['domains']:
            self.site_to_domain_map[dom['site_url'].replace('.co','')] = dom['id']
            ret_domain = json.loads(self.req.get(self.base + 'countries?domain='+dom['id']+'&apikey=' + self.api_key).content)
            ret_domain_us = json.loads(self.req.get(self.base + 'countries?lang=en-us&domain='+dom['id']+'&apikey=' + self.api_key).content)
            dom_country_to_id_map = {dom['name']:dom['id'] for dom in ret_domain['countries']}
            dom_id_to_country_map = {dom['id']:dom['name'] for dom in ret_domain_us['countries']}
            for k,v in dom_country_to_id_map.items():
                if k not in self.country_to_country_map and k != dom_id_to_country_map[v]:
                    self.country_to_country_map[k] = dom_id_to_country_map[v]

            ret_domain = json.loads(self.req.get(self.base + 'cities?domain='+dom['id']+'&apikey=' + self.api_key).content)
            ret_domain_us = json.loads(self.req.get(self.base + 'cities?lang=en-us&domain='+dom['id']+'&apikey=' + self.api_key).content)
            dom_city_to_id_map = {dom['name']:dom['id'] for dom in ret_domain['cities']}
            dom_id_to_city_map = {dom['id']:dom['name'] for dom in ret_domain_us['cities']}
            for k,v in dom_city_to_id_map.items():
                if k not in self.city_to_city_map and k != dom_id_to_city_map[v]:
                    self.city_to_city_map[k] = dom_id_to_city_map[v]
        if save:
            pickle.dump((self.site_to_domain_map, self.city_to_city_map, self.country_to_country_map), open('tm_maps.pkl','wb'))

    def get_event_from_url(self, tm_url):
        eventid = tm_url.split('event/')[-1].split('/')[-1]
        base_url = tm_url.replace('https://','').replace('https://','').split('/')[0]
        if base_url not in self.site_to_domain_map:
            raise ValueError('URL is not associated with ticketmaster international')

        ret = json.loads(self.req.get(self.base + 'events/' + eventid + "?"
                                      + 'lang=en-en'
                                      + '&domain='+self.site_to_domain_map[base_url]
                                      + '&apikey='+self.api_key).content)
        row = self.parse_single_event(ret)
        return pd.Series(row)


    def get_events(self, params=None, event_limit=20):
        if params is not None:
            params_str = '&'.join([k+'='+str(v) for k,v in params.items(())])
        else:
            params_str = ''

        events=[]
        current_event_limit = 0
        for domain in self.site_to_domain_map.values():
            ret = json.loads(self.req.get(self.base+'events?'+params_str+ '&domain='+domain+self.default_params).content)
            num_events = ret['pagination']['total']
            print('Total possible events in domain='+domain+' is', num_events)
            current_events = ret['pagination']['start']+ret['pagination']['rows']
            for i in range(len(ret['events'])):
                ret['events'][i]['sample_time'] = datetime.datetime.now(datetime.datetime.now().astimezone().tzinfo)
            events += ret['events']
            if event_limit is None or current_event_limit > num_events:
                current_event_limit = num_events
            else:
                current_event_limit = event_limit
            while current_events < current_event_limit:
                if np.mod(current_events, np.floor(current_event_limit / 10)) == 0:
                    print('parsing for domain='+domain+' is', 100 * current_events / current_event_limit, 'percent complete')
                ret = json.loads(self.req.get(self.base + 'events?' + params_str + '&domain='+domain+
                                              '&start='+str(current_events)+self.default_params).content)
                if 'events' not in ret:
                    continue
                for i in range(len(ret['events'])):
                    ret['events'][i]['sample_date'] = datetime.datetime.now(datetime.datetime.now().astimezone().tzinfo)
                current_events = ret['pagination']['start']+ret['pagination']['rows']
                events += ret['events']
        print('Found',len(events),'events')
        return events

    def add_availability_info(self, event_row):
        avail = {'avail_checked':True}
        try:
            ret = json.loads(self.req.get(self.base + 'events/' + event_row['ticketmaster_event_id'] + '/prices?' + '&domain='+ event_row['domain'] + self.default_params).content)
        except json.decoder.JSONDecodeError:
            return avail
        if 'errors' in ret:
            return avail
        for price_type in ret['event']['price_types']:
            if price_type['regular']:
                if 'currency' in event_row:
                    convertion_rate = self.forex.get_rate(event_row['currency'], 'USD')
                else:
                    convertion_rate = np.nan
                price_levels = pd.DataFrame(price_type['price_levels']).sort_values('face_value', ascending=False)
                avail['avail_first_tier'] = price_levels.iloc[0]['availability']
                avail['price_first_tier'] = price_levels.iloc[0]['face_value']*convertion_rate
                avail['price_mean'] = price_levels['face_value'].mean()*convertion_rate
                avail['price_median'] = price_levels['face_value'].median()*convertion_rate
                avail['avail_mode'] = price_levels['availability'].mode()[0]
                avail['price_last_tier'] = price_levels.iloc[-1]['face_value'] * convertion_rate
                avail['avail_last_tier'] = price_levels.iloc[-1]['availability']
                avail['avail_some_sold_out'] = bool((price_levels['availability']=='none').any())
                avail['avail_all_sold_out'] = bool((price_levels['availability']=='none').all())
                avail['avail_percent_sold_out_types'] = sum(price_levels['availability']=='none')/price_levels.shape[0]
                avail['avail_types_sold_out'] = ','.join(price_levels.loc[price_levels['availability']=='none','name'].tolist())
                price_levels['prop_face_values'] = price_levels['face_value']/price_levels['face_value'].sum()
                avail['avail_dollar_sold_metric'] = price_levels.loc[price_levels['availability']=='none','prop_face_values'].sum()
                price_levels['idx'] = price_levels.index/price_levels.shape[0]
                avail['avail_rank_sold_metric'] = price_levels.loc[price_levels['availability']=='none', 'idx'].mean()
        return pd.Series(avail)

    def parse_single_event(self, event_raw):
        if ('attractions' not in event_raw) or ('categories' not in event_raw) or ('event_date' not in event_raw):
            return None
        row = {}
        row['ticketmaster_event_id'] = event_raw['id']
        row['performers'] = event_raw['attractions'][0]['name']  # TODO is getting the first ok?
        row['cat'] = event_raw['categories'][0]['id']  # TODO same here
        row['domain'] = event_raw['domain']
        row['subcat'] = event_raw['categories'][0]['subcategories'][0]['id']
        row['timezone'] = event_raw['timezone']
        timezone = pytz.timezone(event_raw['timezone'])
        on_sale_date = datetime.datetime.strptime(event_raw['on_sale_date']['value'], '%Y-%m-%dT%H:%M:%SZ')
        on_sale_date = pytz.utc.localize(on_sale_date)
        on_sale_date = on_sale_date.astimezone(timezone)
        row['on_sale_date'] = on_sale_date
        eventdate = datetime.datetime.strptime(event_raw['event_date']['value'], '%Y-%m-%dT%H:%M:%SZ')
        eventdate = pytz.utc.localize(eventdate)
        eventdate = eventdate.astimezone(timezone)
        row['event_date'] = eventdate
        row['currency'] = event_raw['currency']
        row['sold_out'] = event_raw['properties']['sold_out']
        # if event_raw['properties']['cancelled'] or event_raw['properties']['rescheduled']:
        #     return None
        row['seats_available'] = event_raw['properties']['seats_available']
        address = event_raw['venue']['location']['address']
        row['lat'] = address['lat'] if 'lat' in address else None
        row['long'] = address['long'] if 'long' in address else None
        row['country'] = address['country'] if 'country' in address else None
        row['city'] = address['city'] if 'city' in address else None
        row['venue'] = event_raw['venue']['name']
        row['venue_id'] = event_raw['venue']['id']
        row['event_url'] = event_raw['url']
        row['ticketmaster_venue_id'] = event_raw['venue']['id']
        row['sample_date'] = event_raw['sample_date'] \
            if 'sample_date' in event_raw \
            else pd.to_datetime(datetime.datetime.now(datetime.datetime.now().astimezone().tzinfo))
        return row

    def parse_events_to_df(self, events_raw):
        print('There are', len(events_raw), 'events')
        event_cont = []
        total_events = len(events_raw)
        for event_idx, event_raw in enumerate(events_raw):
            if np.mod(event_idx, np.floor(total_events / 10)) == 0:
                print('parsing is', 100 * event_idx / total_events, 'percent complete')
            try:
                row = self.parse_single_event(event_raw)
                if row is None or row['lat'] is None or row['long'] is None:
                    continue
                event_cont.append(pd.Series(row))
            except (ValueError, KeyError):
                pass
        all_events = pd.concat(event_cont, axis=1).T.reset_index(drop=True)
        print('parsing is 100 percent complete. There are', all_events.shape[0],'events')
        return all_events

    @staticmethod
    def get_time_features_for_event(event):
        row_out = {}
        row_out['day_of_week'] = days_of_week[event['event_date'].weekday()]
        row_out['time_of_day'] = event['event_date'].hour
        row_out['on_sale_period'] = (event['event_date'] - event['on_sale_date']).total_seconds() / 60 / 60 / 24
        row_out['days_to_event'] = (event['event_date'] - event[
            'sample_date'].to_pydatetime()).total_seconds() / 60 / 60 / 24
        row_out['days_on_sale'] = (event['sample_date'].to_pydatetime() - event[
            'on_sale_date']).total_seconds() / 60 / 60 / 24
        row_out['event_complete'] = row_out['days_to_event'] < 0
        if row_out['event_complete']:
            row_out['days_on_sale'] = row_out['on_sale_period']
            row_out['days_to_event'] = np.nan
        return pd.Series(row_out)


if __name__=='__main__':
    tm = TicketMaster()
    #tm.get_events()
    # json.dump(events,
    #             open('../../data/tickemaster_'+str(len(events))+'_event_scrap_'+datetime.datetime.now().strftime('%d-%m-%Y')+'.pkl','wb'))
    # print('All data downloaded')
    #events = pickle.load(open('../../data/tickemaster_7489_event_scrap_15-09-2019.pkl','rb'))
    # events_df = tm.parse_events_to_df(events)
    # print('All data parsed')
    # events_df.to_csv(os.path.join(my_file,'../../data/ticketmaster'+datetime.datetime.now().strftime('%d-%m-%Y')+'.csv'), index=False)
    # events_df.to_pickle(os.path.join(my_file,'../../data/ticketmaster'+datetime.datetime.now().strftime('%d-%m-%Y')+'.pkl'))
    events = pd.read_pickle('../../data/events_22-09-2019.pkl')
    avail = tm.add_availability_info(events.iloc[4])
    print(avail)