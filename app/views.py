from flask import render_template, request
from app import app
import MySQLdb as mdb

from test_model import ModelIt

#Read login info
f = open('login.txt')
login = f.read()
f.close()
login = login.split()
db = mdb.connect(login[0],login[1],login[2],'indiedb')
charset = 'utf8'

@app.route('/')
@app.route('/index')
def index():
   user = { 'nickname': 'Miguel' } # fake user
   return render_template("index.html",
       title = 'Home',
       user = user)

@app.route('/db')
def games_page():
    with db:
        cur = db.cursor()
        cur.execute("SELECT title FROM Games LIMIT 15;")
        query_results = cur.fetchall()
    games = ""
    for result in query_results:
        games += result[0]
        games += "<br>"
    return games

@app.route("/db_fancy")
def games_page_fancy():
    with db:
        cur = db.cursor()
        cur.execute("SELECT title, creator, game_type, rating \
             FROM Games ORDER BY votes DESC LIMIT 15;")

        query_results = cur.fetchall()
    games = []
    for result in query_results:
        games.append(dict(title=result[0], creator=result[1], game_type=result[2], rating=result[3]))
    return render_template('games.html', games=games)

@app.route('/output')
def games_output():
  #pull 'ID' from input field and store it
  game = request.args.get('ID')

  with db:
    cur = db.cursor()
    #just select the city from the world_innodb that the user inputs
    cur.execute("SELECT title, creator, game_type, rating FROM Games WHERE title='%s';" % game)
    query_results = cur.fetchall()

  games = []
  for result in query_results:
    games.append(dict(title=result[0], creator=result[1], game_type=result[2], rating=result[3]))

  if len(games) == 0:
     rating_input = 0
  else:
     rating_input = games[0]['rating']
  the_result = ModelIt(game,rating_input)
  return render_template("output.html", games = games, the_result = the_result)

