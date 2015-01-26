from flask import render_template, request
from app import app
from recommender import recommend_games
import MySQLdb as mdb

from login_script import login_mysql

#Read login info
db = login_mysql('login.txt')
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
    
    titles, game_types, themes, ratings, sim_ratings = recommend_games.run_everything_on_input_title(game,cur)

  games = []
  for i in range(len(titles)):
    games.append(dict(title=titles[i], game_type=game_types[1], theme=themes[i], rating=ratings[i],
                      sim_rating=sim_ratings[i]))

  return render_template("output.html", big_game = game, games = games)

