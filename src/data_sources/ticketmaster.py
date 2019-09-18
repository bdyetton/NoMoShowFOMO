import requests
import json
import datetime
import pandas as pd
#from tzwhere import tzwhere
import pytz
import os
import numpy as np
import pickle
import time
my_file = os.path.dirname('__file__')

class TicketMaster():
    def __init__(self):
        #self.tzwhere = tzwhere.tzwhere()
        self.base = 'https://app.ticketmaster.eu/mfxapi/v2/'
        self.api_key = os.environ['api_key']
        self.default_params = '&lang=en-en'+\
                              '&category_ids=10001' +\
                              '&is_not_package=true' +\
                              '&exlude_external=true' +\
                              '&min_price=1' +\
                              '&apikey='+self.api_key #&domain=canada
        self.req = requests.session()

    def get_events(self, params=None, event_limit=20):
        if params is not None:
            params_str = '&'.join([k+'='+str(v) for k,v in params.items(())])
        else:
            params_str = ''
        ret = json.loads(self.req.get(self.base+'events?'+params_str+self.default_params).content)
        num_events = ret['pagination']['total']
        print('Total possible events is', num_events)
        current_events = ret['pagination']['start']+ret['pagination']['rows']
        events = ret['events']
        if event_limit is None or event_limit > num_events:
            event_limit = num_events
        while current_events < event_limit:
            time.sleep(0.2)
            if np.mod(current_events, np.floor(event_limit / 10)) == 0:
                print('parsing is', 100 * current_events / event_limit, 'percent complete')
            ret = json.loads(self.req.get(self.base + 'events?' + params_str +
                                          '&start='+str(current_events)+self.default_params).content)
            for i in range(len(ret['events'])):
                ret['events'][i]['sample_time'] = datetime.datetime.now()
            current_events = ret['pagination']['start']+ret['pagination']['rows']
            events += ret['events']
        return events

    def add_availability_info(self, event_row):
        avail = {}
        try:
            ret = json.loads(self.req.get(self.base + 'events/' + event_row['ticketmaster_event_id'] + '/prices?' + '&domain='+ event_row['domain'] + self.default_params).content)
        except json.decoder.JSONDecodeError:
            return avail
        if 'errors' in ret:
            return avail
        for price_type in ret['event']['price_types']:
            if price_type['regular']:
                price_levels = pd.DataFrame(price_type['price_levels']).sort_values('face_value', ascending=False)
                avail['avail_first_tier'] = price_levels.iloc[0]['availability']
                avail['avail_mode'] = price_levels['availability'].mode()[0]
                if price_levels.shape[0] > 0:
                    avail['avail_last_tier'] = price_levels.iloc[-1]['availability']
                else:
                    avail['avail_last_tier'] = None
                avail['avail_some_sold_out'] = bool((price_levels['availability']=='none').any())
                avail['avail_all_sold_out'] = bool((price_levels['availability']=='none').all())
                avail['avail_percent_sold_out_types'] = sum(price_levels['availability']=='none')/price_levels.shape[0]
                avail['avail_types_sold_out'] = ','.join(price_levels.loc[price_levels['availability']=='none','name'].tolist())
                price_levels['prop_face_values'] = price_levels['face_value']/price_levels['face_value'].sum()
                avail['avail_dollar_sold_metric'] = price_levels.loc[price_levels['availability']=='none','prop_face_values'].sum()
                price_levels['idx'] = price_levels.index/price_levels.shape[0]
                avail['avail_rank_sold_metric'] = price_levels.loc[price_levels['availability']=='none', 'idx'].mean()

        return avail

    def parse_events_to_df(self, events_raw):
        event_cont = []
        total_events = len(events_raw)
        for event_idx, event_raw in enumerate(events_raw):
            if np.mod(event_idx, np.floor(total_events / 10)) == 0:
                print('parsing is', 100 * event_idx / total_events, 'percent complete')
            try:
                if ('attractions' not in event_raw) or ('categories' not in event_raw) or ('event_date' not in event_raw):
                    continue
                row = {}
                row['ticketmaster_event_id'] = event_raw['id']
                row['performers'] = event_raw['attractions'][0]['name'] #TODO is getting the first ok?
                row['cat'] = event_raw['categories'][0]['id'] #TODO same here
                row['domain'] = event_raw['domain']
                row['subcat'] = event_raw['categories'][0]['subcategories'][0]['id']
                row['timezone'] = event_raw['timezone']
                timezone = pytz.timezone(event_raw['timezone'])
                on_sale_date = datetime.datetime.strptime(event_raw['on_sale_date']['value'],'%Y-%m-%dT%H:%M:%SZ')
                on_sale_date = pytz.utc.localize(on_sale_date)
                on_sale_date = on_sale_date.astimezone(timezone)
                row['on_sale_date'] = on_sale_date
                eventdate = datetime.datetime.strptime(event_raw['event_date']['value'], '%Y-%m-%dT%H:%M:%SZ')
                eventdate = pytz.utc.localize(eventdate)
                eventdate = eventdate.astimezone(timezone)
                row['event_date'] = eventdate
                row['currency'] = event_raw['currency']
                address = event_raw['venue']['location']['address']
                row['lat'] = address['lat'] if 'lat' in address else None
                row['long'] = address['long'] if 'long' in address else None
                row['country'] = address['country'] if 'country' in address else None
                row['city'] = address['city'] if 'city' in address else None
                row['venue'] = event_raw['venue']['name']
                row['ticketmaster_venue_id'] = event_raw['venue']['id']
                row['sample_date'] = datetime.datetime.now(datetime.datetime.now().astimezone().tzinfo)
                event_cont.append(pd.Series(row))
            except (ValueError, KeyError):
                pass
        return pd.concat(event_cont, axis=1).T


if __name__=='__main__':
    tm = TicketMaster()
    events = tm.get_events(event_limit=8000)
    pickle.dump(events,
                open('../../data/tickemaster_'+str(len(events))+'_event_scrap_'+datetime.datetime.now().strftime('%d-%m-%Y')+'.pkl','wb'))
    print('All data downloaded')
    # events = pickle.load(open('../../data/tickemaster_7489_event_scrap_15-09-2019.pkl','rb'))
    # events_df = tm.parse_events_to_df(events)
    # print('All data parsed')
    # events_df.to_csv(os.path.join(my_file,'../../data/ticketmaster'+datetime.datetime.now().strftime('%d-%m-%Y')+'.csv'), index=False)
    # events_df.to_pickle(os.path.join(my_file,'../../data/ticketmaster'+datetime.datetime.now().strftime('%d-%m-%Y')+'.pkl'))