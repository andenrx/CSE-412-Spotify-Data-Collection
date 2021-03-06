from website import app
from flask import render_template, request, g, redirect, make_response
import os
import sys
from website.custom_scripts import *

# NOTE: g is a flask global variable for the current context.
@app.route("/", methods=["GET", "POST"])
def main_page():
    if request.method == "GET":
        return render_template("index.html", prev=["", "", ""])
    elif request.method == "POST":
        # logic for querying database and return data
        search_string = request.form['inputString']
        query_type = request.form['inputQuery']
        sort_by_type = request.form['sortby']
        prev_query = [search_string, query_type, sort_by_type]
        if search_string == "":
            return render_template("index.html", prev=["", "", ""], songs=query_db.list_all(get_db().cursor(), sort_by_type))
        else:
            return render_template("index.html", prev=prev_query, songs=query_db.search_by(get_db().cursor(), search_string, query_type, sort_by_type))

@app.route("/artist", methods=["GET"])
def artist_page():
    if request.method != "GET":
        print(f"/songs-by-artist received a {request.method} request when it should have received a 'GET' request.")
        return error_page()
    artist = request.args.get("artist", "")
    if not artist:
        print(f"/songs-by-artist needs to receive an 'artist' parameter (eg. /songs-by-artist?artist=bob)")
        return error_page()
    return render_template("index.html", prev=["", "", ""], songs=query_db.songs_by_artist(get_db().cursor(), artist))

@app.route("/selected-song", methods=["GET"])
def song_page():
    # Will need to implement method for POST (for submitting ratings/comments)
    if request.method != "GET":
        print(f"/selected-song received a {request.method} request when it should have received a 'GET' request.")
        return error_page()
    song_id = request.args.get("song_id", "")

    if not song_id:
        print(f"/selected-song needs to receive an 'song_id' parameter. How did you get here?")
        return error_page()

    # Will want to put query here that gets all comments

    # For template, want to pass in array of all comments (from query results)
    return render_template("songpage.html")

@app.route("/rate", methods=["GET", "POST"])
def rate_song_page():
    if request.method == "GET":
        user_id = request.cookies.get('user_id')
        if not user_id:
            print('user_id', user_id)
            return redirect("/sign-in")
        song_id = request.args.get("song_id", "")
        if not song_id:
            print("/rate needs to receive a song_id parameter (eg. /rate?song=123)")
            return error_page()
        results = query_db.rate_song_page(get_db().cursor(), song_id)
        if not results:
            print(f"/rate was unable to find any songs with id '{song_id}'")
            return error_page()
        return render_template("rate.html", song_id=song_id, song_name=results[0].song_name, results=results)
    else:
        user_id = request.cookies.get('user_id')
        if not user_id:
            print('user_id', user_id)
            return redirect("/sign-in")
        song_id = request.form["song_id"]
        if not song_id:
            print(f"/rate/ expected to recieve a song_id")
        rating = request.form['rating']
        comment = request.form['comment']
        if not rating.isdigit():
            print(f"/rate/ expected the rating to be an integer, but instead received '{rating}'")
            return error_page()
        rating = int(rating)
        if not 1 <= rating <= 10:
            print(f"/rate/ expected the rating to be between 1 and 10, but instead received '{rating}'")
            return error_page()
        query_db.rate(get_db(), user_id, song_id, rating, comment)
        return redirect("/")

@app.route("/sign-in", methods=["GET", "POST"])
def log_in():
    if request.method == "GET":
        return render_template("sign-in.html")
    else:
        username = request.form['username']
        password = request.form['password']
        user_id = query_db.get_or_create_uid(get_db(), username=username, password=password)
        page = make_response(redirect("/"))
        page.set_cookie('user_id', user_id)
        page.set_cookie('username', username)
        return page

@app.route("/sign-out", methods=["GET"])
def log_out():
    page = redirect(request.referrer)
    page.set_cookie('userID', "")
    page.set_cookie('username', "")
    return page

def error_page():
    return "FUCK" # should be a template or something

@app.errorhandler(404)
def error404(error):
    print(error)
    return error_page()

class DotDict(dict):
    def __getattr__(self, key):
        if key not in self:
            print(f"There was an error while trying to access '{key}' from {self}")
            return "Database Error"
        else:
            return self[key]

def get_db():
    """
    Opens a new connection to the DB if there is none for the current context.
    """
    if not hasattr(g, 'postgres_db'):
        g.postgres_db = query_db.init_db_connection()
    return g.postgres_db


@app.teardown_appcontext
def close_db(input):
    """
    Closes the database again at the end of the request.
    """
    if hasattr(g, 'postgres_db'):
        g.postgres_db.close()
