from src.data_sources.ticketmaster import TicketMaster
import datetime
import pickle
from time import sleep
tm = TicketMaster()
time_started = datetime.datetime.now() - datetime.timedelta(days=1)
while True:
    if datetime.datetime.now() - time_started > datetime.timedelta(days=1):
        time_started = datetime.datetime.now()
        print('Grabbing Events')
        events = tm.get_events()
        pickle.dump(events,
                    open('../../data/tickemaster_' + str(len(events)) + '_event_scrap_' + datetime.datetime.now().strftime(
                        '%d-%m-%Y') + '.pkl', 'wb'))
    sleep(60*60)
    print('sleeping')