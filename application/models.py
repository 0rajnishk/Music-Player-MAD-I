
from application.database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    city = db.Column(db.String(128))
    role = db.Column(db.String(128), default='user', nullable=False)
    playlist_song = db.Table('playlist_song',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id')),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'))
)
    def __init__(self, email, password, name, city, role):
        self.email = email
        self.password = password
        self.name = name
        self.city = city
        self.role = role

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    genre = db.Column(db.String(128))
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)  # Add artist_id
    songs = db.relationship('Song', backref='album', lazy=True, primaryjoin='Album.id == Song.album_id')

    def __init__(self, name, genre, artist_id):
        self.name = name
        self.genre = genre
        self.artist_id = artist_id

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.LargeBinary)  # Use LargeBinary for binary data like images
    name = db.Column(db.String(128), unique=True, nullable=False)
    genre = db.Column(db.String(128), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    date = db.Column(db.String)
    lyrics = db.Column(db.String(128), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False)
    ratings = db.relationship('SongRating', backref='song', lazy=True)

    def __init__(self, name, genre, duration, artist_id, image, date, lyrics):
        self.name = name
        self.genre = genre
        self.duration = duration
        self.artist_id = artist_id
        self.image = image
        self.date = date
        self.lyrics = lyrics

class Artist (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    genre = db.Column(db.String(128))
    albums = db.relationship('Album', backref='artist', lazy=True)

    def __init__(self, name, genre):
        self.name = name
        self.genre = genre


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    songs = db.relationship('Song', secondary='playlist_song', backref='playlists', lazy='dynamic')

    def __init__(self, name, user_id):
        self.name = name
        self.user_id = user_id

class SongRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    def __init__(self, user_id, song_id, rating):
        self.user_id = user_id
        self.song_id = song_id
        self.rating = rating
