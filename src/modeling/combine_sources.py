import pandas as pd
import os
my_file = os.path.dirname('__file__')
import src.data_sources.songkick as songkick
import src.data_sources.google_trends as google_trends
import src.data_sources.demographics as demographics
import src.data_sources.ticketmaster as ticketmaster
import numpy as np
import sys
import time
import pickle
from multiprocessing.pool import ThreadPool
from multiprocessing.pool import Pool
from threading import Thread
from queue import Queue, Empty
debug = False


def add_songkick_threaded(df):
    num_splits = 4
    dfs = np.array_split(df, num_splits)
    pool = Pool(processes=num_splits)
    names = [str(i) for i in range(num_splits)]
    sk_dfs = pool.map(add_songkick, (zip(dfs, names), basedate))
    return pd.concat(sk_dfs)


def add_songkick(df, basedate):
    if isinstance(df, tuple):
        df = df[0]
        thread_name = '_'+df[1]+'_'
    else:
        thread_name = ''
    try:
        existing_df = pd.read_pickle('../../data/songkick_temp' + basedate + '.pkl').set_index('idx')
        already_done = df.index.isin(existing_df.index)
        not_done_df = df.loc[~already_done, :]
        existing_df = existing_df.reset_index()

    except FileNotFoundError:
        not_done_df = df
        existing_df = pd.DataFrame()

    print('total records are', df.shape[0], 'with')
    print(not_done_df.shape[0], 'records not done')
    sk = songkick.SongKick()
    sk_cont = []
    print('running sk for ', not_done_df.shape[0],'records')
    idx_real = 0
    for idx, row in not_done_df.iterrows():
        idx_real += 1
        if np.mod(idx_real, np.floor(df.shape[0] / 100)) == 0:
            print('SK is', np.floor(100 * idx_real / not_done_df.shape[0]), 'percent complete')
            sk_df = pd.concat(sk_cont, axis=1).T
            sk_df = pd.concat([sk_df, existing_df])
            #sk_df = sk_df.set_index('idx')
            sk_df.to_pickle('../../data/songkick_temp'+basedate+thread_name+'.pkl')
        try:
            venue_series = sk.get_songkick_data_for_event(row)
        except KeyboardInterrupt:
            print('------------keyboard interrupt------------')
            return
        except BaseException as e:
            if not debug:
                print(idx, e)
                continue
            else:
                raise
        venue_series['idx'] = idx
        sk_cont.append(venue_series)
    sk_df = pd.concat(sk_cont, axis=1).T
    sk_df = pd.concat([sk_df, existing_df])
    sk_df = sk_df.set_index('idx')
    return sk_df


def add_ticket_levels(df):
    tm = ticketmaster.TicketMaster()
    tm_cont = []
    print('running avail for ', df.shape[0], 'records')
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('TM is', 100 * idx / df.shape[0], 'percent complete')
        try:
            row_out = tm.add_availability_info(row)
            row_out['idx'] = idx
            tm_cont.append(row_out)
        except KeyboardInterrupt:
            return
        except BaseException as e:
            if not debug:
                print(e)
                continue
            else:
                raise
    tm_df = pd.concat(tm_cont, axis=1).T
    tm_df = tm_df.set_index('idx')
    return tm_df

def add_time_features(df):
    tm = ticketmaster.TicketMaster()
    tm_cont = []
    print('running time for ', df.shape[0], 'records')
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('Time is', 100 * idx / df.shape[0], 'percent complete')
        try:
            row_out = tm.get_time_features_for_event(row)
            row_out['idx'] = idx
            tm_cont.append(row_out)
        except KeyboardInterrupt:
            return
        except BaseException as e:
            if not debug:
                print(e)
                continue
            else:
                raise
    tm_df = pd.concat(tm_cont, axis=1).T
    tm_df = tm_df.set_index('idx')
    return tm_df

def add_local_popularity(df, basedate, use_proxies):
    if not use_proxies:
        num_splits = 1
    else:
        num_splits = 5
    try:
        existing_df = pd.read_pickle('../../data/trends_'+basedate+'.pkl')
        already_done = df.index.isin(existing_df.index)
        not_done_df = df.loc[~already_done, :]
    except FileNotFoundError:
        not_done_df = df
        existing_df = pd.DataFrame()

    print('total records are', df.shape[0],'with')
    print(not_done_df.shape[0], 'records not done')
    dfs = np.array_split(not_done_df, num_splits)
    q_in = Queue(maxsize=num_splits*3)
    q_out = Queue()
    pg = google_trends.ProxyGrenerator(q_in)
    thread_cont = []
    tr_dfs_cont = [existing_df]
    for thread_idx in range(num_splits):
        th = Thread(target=local_pop_thread_run, args=(dfs[thread_idx], q_in, q_out, use_proxies))
        th.start()
        thread_cont.append(th)

    all_alive = True
    last_proxy_ticker = 0
    while all_alive:
        for thread in thread_cont:
            all_alive &= thread.isAlive()
        if use_proxies:
            pg.check_for_new_proxies()
            last_proxy_ticker += 1
            if last_proxy_ticker > 60:
                pg.save_proxylist()
                last_proxy_ticker = 0
        try:
            new_data = q_out.get_nowait()
        except Empty:
            time.sleep(1)
            continue
        tr_dfs_cont.append(new_data)
        tr_df = pd.concat(tr_dfs_cont, sort=True)
        tr_df.to_pickle('../../data/trends_' + basedate + '.pkl')
        time.sleep(1)
    return pd.concat(tr_dfs_cont, sort=True)


def local_pop_thread_run(df, q_in, q_out, use_proxy):
    gt = google_trends.Trends(q_in, use_proxy=use_proxy)
    gt_cont = []
    print('running popularity for ', df.shape[0], 'records')
    idx_real = 0
    for idx, row in df.iterrows():
        idx_real += 1
        if np.mod(idx_real, 20) == 0:
            print('Got 20, returning to main loop')
            gt_df = pd.concat(gt_cont, axis=1).T
            gt_df = gt_df.set_index('idx')
            q_out.put(gt_df)
            gt_cont = []
        try:
            row_out = gt.get_geo_trends(row['performers'], 'today 5-y', gt.get_iso_region(row['lat'],row['long']))
            row_out['idx'] = idx
            gt_cont.append(row_out)
        except ValueError as e:
            print('Got ValueError:', e)
            continue
        except KeyboardInterrupt:
            return
        except Exception as e:
            print(idx)
            if not debug:
                print(e)
                continue
            else:
                raise
    gt_df = pd.concat(gt_cont, axis=1).T
    gt_df = gt_df.set_index('idx')
    q_out.put(gt_df)

def add_availability(df):
    tm = ticketmaster.TicketMaster()

    tm_cont = []
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('Avail is', 100 * idx / df.shape[0], 'percent complete')
        try:
            if 'avail_checked' in row.index and row['avail_checked']:
                continue
            row_out = tm.add_availability_info(row)
            row_out['idx'] = idx
            tm_cont.append(pd.Series(row_out))
        except KeyboardInterrupt:
            return
        except BaseException as e:
            if not debug:
                print(e)
                continue
            else:
                raise
    tm_df = pd.concat(tm_cont, axis=1).T
    tm_df = tm_df.set_index('idx')
    return tm_df

def parse_events(events):
    tm = ticketmaster.TicketMaster()
    events = tm.parse_events_to_df(events)
    print('Got', events.shape[0],'records')
    return events

def add_demographics(df):
    tm = ticketmaster.TicketMaster()
    dg = demographics.Demographics(tm.city_to_city_map, tm.country_to_country_map)
    dg_cont = []
    print('running demo for ', df.shape[0], 'records')
    for idx, row in df.iterrows():
        if np.mod(idx, np.floor(df.shape[0] / 10)) == 0:
            print('Demo is', 100 * idx / df.shape[0], 'percent complete')
        try:
            row_out = dg.get_pop(row['city'], row['country'])
            row_out['idx'] = idx
            dg_cont.append(row_out)
        except KeyboardInterrupt:
            return
        except BaseException as e:
            if not debug:
                print(e)
                continue
            else:
                raise
    dg_df = pd.concat(dg_cont, axis=1).T
    dg_df = dg_df.set_index('idx')
    return dg_df

if __name__ == '__main__':
    basedate = sys.argv[1]
    routine = sys.argv[2]
    if routine == 'get_events':
        print('getting_events')
        tm = ticketmaster.TicketMaster()
        events = tm.get_events(event_limit=None)
        pickle.dump(events, open('../../data/tickemaster_event_scrap_'+basedate+'.pkl','wb'))
    if routine == 'parse_events':
        print('parsing_events')
        events = pd.read_pickle(os.path.join(my_file,'../../data/tickemaster_event_scrap_'+basedate+'.pkl'))
        df = parse_events(events)
        df.to_pickle('../../data/events_'+basedate+'.pkl')
    if routine == 'avail':
        df_events = pd.read_pickle('../../data/events_' + basedate + '.pkl')
        df = add_availability(df_events)
        df = pd.merge(df, df_events, right_index=True, left_index=True)
        df = df.loc[df['avail_first_tier']!='unknown',:]
        df.to_pickle('../../data/events_and_avail_'+basedate+'.pkl')
    if routine == 'songkick':
        df_events = pd.read_pickle('../../data/events_and_avail_' + basedate + '.pkl')
        df = add_songkick(df_events, basedate)
        df.to_pickle('../../data/songkick_'+basedate+'.pkl')
    if routine == 'time':
        df_events = pd.read_pickle('../../data/events_and_avail_' + basedate + '.pkl')
        df = add_time_features(df_events)
        df.to_pickle('../../data/time_'+basedate+'.pkl')
    if routine == 'popularity':
        df_events = pd.read_pickle('../../data/events_and_avail_' + basedate + '.pkl')
        df = add_local_popularity(df_events, basedate, use_proxies=True)
        df.to_pickle('../../data/popularity_'+basedate+'.pkl')
    if routine == 'demographics':
        df_events = pd.read_pickle('../../data/events_and_avail_' + basedate + '.pkl')
        df = add_demographics(df_events)
        df.to_pickle('../../data/demographics_'+basedate+'.pkl')
    if routine == 'combine':
        df_base = pd.read_pickle('../../data/events_and_avail_' + basedate + '.pkl')
        for table in ['demographics','songkick','time']:
            df = pd.read_pickle('../../data/'+table+'_'+basedate+'.pkl')
            df_base = pd.merge(df_base, df, right_index=True, left_index=True)
        df_base.to_pickle('../../data/combined_'+basedate+'.pkl')

