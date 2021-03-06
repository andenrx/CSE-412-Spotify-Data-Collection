import psycopg2

def test():
    print("hello")
    return

# Initiates connection to DB server, returns a connection
def init_db_connection():
    import website.config as config
    connection = psycopg2.connect(
        host = config.host,
        port = config.port,
        user = config.user,
        password = config.password,
        database = config.database
    )
    return connection

def list_all(cursor, sort_by_type):
    # function that list all the songs when the search bar is empty
    sort_by_str = sort_by_parser(sort_by_type)
    unprocessed_query = (
        f"SELECT song_name AS title, artist_name AS artist, album_name AS album, avg_table.avg_rating AS average, count_table.total AS num_listens, song.song_id AS song_id "\
        f"FROM song, artist, performed_by, album, is_in, "\
        f"    ( "\
        f"        SELECT song.song_id, ROUND(AVG(rates.rating_value),2) AS avg_rating "\
        f"        FROM song, rates "\
        f"        WHERE song.song_id = rates.song_id "\
        f"        GROUP BY song.song_id "\
        f"    ) AS avg_table, "\
        f"    ( "\
        f"        SELECT song.song_id, COUNT(*) AS total "\
        f"        FROM song, listens_to "\
        f"        WHERE song.song_id = listens_to.song_id "\
        f"        GROUP BY song.song_id "\
        f"    ) AS count_table "\
        f"WHERE song.song_id = performed_by.song_id  "\
        f"    AND performed_by.artist_id = artist.artist_id  "\
        f"    AND song.song_id = is_in.song_id  "\
        f"    AND is_in.album_id = album.album_id  "\
        f"    AND avg_table.song_id = song.song_id "\
        f"    AND count_table.song_id = song.song_id "\
        f"ORDER BY {sort_by_str}"
    )
    query = cursor.mogrify(unprocessed_query)
    return execute_query_and_return(cursor, query)

def search_by(cursor, input_str, query_type, sort_by_type): 
    # function that performs a query based on the query type
    sort_by_str = sort_by_parser(sort_by_type)
    unprocessed_query = (
        f"SELECT song_name AS title, artist_name AS artist, album_name AS album, avg_table.avg_rating AS average, count_table.total AS num_listens, song.song_id AS song_id "\
        f"FROM song, artist, performed_by, album, is_in, "\
        f"    ( "\
        f"        SELECT song.song_id, ROUND(AVG(rates.rating_value),2) AS avg_rating "\
        f"        FROM song, rates "\
        f"        WHERE song.song_id = rates.song_id "\
        f"        GROUP BY song.song_id "\
        f"    ) AS avg_table, "\
        f"    ( "\
        f"        SELECT song.song_id, COUNT(*) AS total "\
        f"        FROM song, listens_to "\
        f"        WHERE song.song_id = listens_to.song_id "\
        f"        GROUP BY song.song_id "\
        f"    ) AS count_table "\
        f"WHERE song.song_id = performed_by.song_id  "\
        f"    AND performed_by.artist_id = artist.artist_id  "\
        f"    AND song.song_id = is_in.song_id  "\
        f"    AND is_in.album_id = album.album_id  "\
        f"    AND avg_table.song_id = song.song_id "\
        f"    AND count_table.song_id = song.song_id "\
        f"    AND {query_type}.{query_type}_name ILIKE %s "\
        f"ORDER BY {sort_by_str}"
    )
    query = cursor.mogrify(unprocessed_query, (format_like_query(input_str),))
    return execute_query_and_return(cursor, query)

def songs_by_artist(cursor, artist):
    unprocessed_query = (
        f"SELECT song_name as title, artist_name as artist FROM song, performed_by, artist "\
        f"WHERE song.song_id = performed_by.song_id "\
        f"AND performed_by.artist_id = artist.artist_id "\
        f"AND artist_name='{artist}'"
    )
    query = cursor.mogrify(unprocessed_query)
    return execute_query_and_return(cursor, query)


def rate_song_page(cursor, song_id):
    unprocessed_query = (
        f"SELECT song.song_name AS song_name, user_table.display_name AS username, rates.comment AS comment, rates.rating_value AS rating "\
        f"FROM song, rates, user_table "\
        f"WHERE song.song_id = rates.song_id "\
        f"    AND rates.user_id = user_table.user_id "\
        f"    AND song.song_id = %s"
    )
    query = cursor.mogrify(unprocessed_query, (song_id,))
    return execute_query_and_return(cursor, query)

# TODO: NOT FINISHED!!!!
def get_song_info(cursor, song_id):
    unprocessed_query = (
        f"SELECT song.song_name AS song_name, "
        f"FROM song, album, artist, is_in, performed_by "
    )

# NOTE: FOR ANY COMMAND TO COMMIT DATA TO THE DATABASE, WE MUST
#       PASS THE CONNECTION, NOT THE CURSOR
def rate(connection, user_id, song_id, rating_value, comment):
    cursor = connection.cursor()
    unprocessed_query = (
        f"INSERT INTO rates (user_id, song_id, rating_value, comment) "\
        f"VALUES (%s, %s, %s, %s) "\
        f"ON CONFLICT DO NOTHING"
    )
    query = cursor.mogrify(unprocessed_query, (user_id, song_id, rating_value, comment))
    cursor.execute(query)
    connection.commit()

def execute_query_and_return(cursor, query):
    cursor.execute(query)
    results = cursor.fetchall()
    keys = [column.name for column in cursor.description]
    return [DotDict({key: data for key, data in zip(keys, row)}) for row in results]

def sort_by_parser(sort_by_type):
    string = ""
    if sort_by_type == "title":
        string = "song_name"
    elif sort_by_type == "artist":
        string = "artist_name"
    elif sort_by_type == "album":
        string = "album_name"
    elif sort_by_type == "popularity":
        string = "popularity DESC"
    return string

def format_like_query(input_str):
    return '%' + input_str + '%'
"""
def get_song_details(cursor, song_id):
    unprocessed_query = 
"""

def get_or_create_uid(connection, username, password):
    print("We currently aren't actually checking passwords, should probably do that")

    cursor = connection.cursor()
    cursor.execute(f"SELECT user_id FROM user_table WHERE display_name='{username}'")
    uid = cursor.fetchone()

    if not uid:
        cursor.execute(f"INSERT INTO user_table (user_id, display_name) VALUES (12345, '{username}') ON CONFLICT DO NOTHING")
        connection.commit()
        cursor.execute(f"SELECT user_id FROM user_table WHERE display_name='{username}'")
        uid = cursor.fetchone()
    return uid[0].strip()

class DotDict(dict):
    def __getattr__(self, key):
        if key not in self:
            print(f"There was an error while trying to access '{key}' from {self}")
            return "Database Error"
        else:
            return self[key]
