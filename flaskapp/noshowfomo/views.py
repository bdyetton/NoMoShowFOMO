from flask import render_template, request
from noshowfomo import app
from noshowfomo.models import predict_from_url

# Python code to connect to Postgres
# You may need to modify this based on your OS,
# as detailed in the postgres dev setup materials.
#user = 'bdyet' #add your Postgres username here
#host = 'localhost'
#dbname = 'birth_db'
#dbpw = 'Nap4life'
#db = create_engine('postgres://%s%s/%s'%(user,host,dbname))
#con = None
#con = psycopg2.connect(database = dbname, user = user, host = host, password = dbpw) #add your Postgres password here

@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/noshowfomo')
def noshowfomo():
    return render_template("noshowfomo.html")

@app.route('/noshowfomo/go')
def noshowfomogo():
  ticketmaster_url = request.args.get('input_url')
  print('Got-------', ticketmaster_url)
  will_sell_out, artist, venue, city, country, event_url = predict_from_url(ticketmaster_url)

  return render_template("noshowfomogo.html", artist=artist,
                         venue=venue, city=city,
                         country=country, will_sell_out=will_sell_out, event_url=event_url)