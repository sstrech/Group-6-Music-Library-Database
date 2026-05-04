# Group 6 Music Library Database

A web-based music library management system built for CSE 412 (Database Management) at Arizona State University, Spring 2026. Users can sign up, search a music catalogue, build and manage playlists, rate songs, follow other users, track listening history, and (as artists) upload new songs to the shared library.

This is **Phase 03** of the project — a full-stack application built on top of the relational schema designed in Phase 01 and implemented in Phase 02.

## Team — Group 6

- Samuel Strechay
- Jairo Lazalde Hernandez
- Saiqa Nawaz
- Alan Escudero

## Tech Stack

- **Frontend:** HTML, CSS, vanilla JavaScript (Fetch API)
- **Backend:** Python 3 + Flask, with Jinja2 templating
- **Database:** PostgreSQL (managed locally with pgAdmin)
- **Auth:** bcrypt password hashing + Flask signed-cookie sessions
- **Config:** python-dotenv for environment variables

## Features

- **Sign up / Log in / Log out** — bcrypt-hashed passwords, server-side sessions
- **Search & Filter** — search the catalogue by song name, artist, album, or genre, with average ratings shown inline
- **Listen History** — play tracking, with the 20 most recent listens shown on the home page
- **Playlists** — create, view, delete playlists; add or remove songs
- **Song Ratings** — rate songs 1–5 stars; ratings can be updated
- **Following** — search for other users and follow / unfollow them
- **Artist Upload** — publish new songs to the shared library

## Setup Instructions

### Prerequisites

- Python 3.10 or newer
- PostgreSQL 14 or newer (with pgAdmin recommended)
- Git

### 1. Clone the repository

```bash
git clone https://github.com/sstrech/Group-6-Music-Library-Database.git
cd Group-6-Music-Library-Database
```

### 2. Install Python dependencies

```bash
pip install flask psycopg2-binary bcrypt python-dotenv
```

### 3. Create the database

In pgAdmin:

1. Create a new database (e.g. `musiclibrary`)
2. Open the Query Tool for that database
3. Open `schema.sql` from this repo, paste it into the Query Tool, and run it (F5) to create the tables
4. Open `datageneration.sql` and run it the same way to populate the database with sample data (500 users, 500 songs, etc.)

### 4. Configure environment variables

Create a file named `.env` in the project root (same folder as `app.py`) with the following keys:

```
DB_NAME=musiclibrary
USERNAME=postgres
PASSWORD=your_postgres_password
HOST=localhost
PORT=5432
SECRET_KEY=any_random_string_will_do
```

Replace `your_postgres_password` with the password you set when installing PostgreSQL. The `.env` file is git-ignored and never committed.

> **Windows note:** if `USERNAME=postgres` doesn't seem to take effect, that's because Windows has a built-in `USERNAME` environment variable. The app uses `load_dotenv(override=True)` to handle this, so make sure your `.env` is saved correctly and Flask is restarted after edits.

### 5. Run the application

```bash
python app.py
```

You should see:

```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

### 6. Open the app

Go to **http://127.0.0.1:5000** in your browser. You'll land on the login / signup page. Sign up a new account, then log in to access the rest of the application.

## Project Structure

```
Group-6-Music-Library-Database/
├── app.py                  # Flask backend with all routes
├── schema.sql              # Database schema (DDL)
├── datageneration.sql      # Sample data (DML)
├── templates/
│   ├── index.html          # Main app (home, search, playlists, following, upload)
│   └── login.html          # Login + signup page
├── .env                    # Environment variables (create this yourself, not committed)
├── .gitignore
└── README.md
```

## Database Schema

The schema consists of 13 relational tables:

| Table          | Description                                    |
|----------------|------------------------------------------------|
| Users          | User accounts (bcrypt password hashes)         |
| Admins         | ISA specialisation of Users                    |
| Artists        | ISA specialisation of Users; created on upload |
| Genres         | Lookup table for genre names                   |
| Songs          | Song catalogue                                 |
| Albums         | Album catalogue                                |
| AlbumSongs     | Many-to-many between Albums and Songs          |
| Playlists      | User-owned playlists                           |
| PlaylistSongs  | Many-to-many between Playlists and Songs       |
| ListenHistory  | Per-user play tracking                         |
| SongRatings    | 1–5 star ratings, one per user per song        |
| AlbumRatings   | 1–5 star ratings, one per user per album       |
| Follows        | User-to-user follow graph                      |

See `schema.sql` for the full DDL with primary keys, foreign keys, and `ON DELETE CASCADE` rules.

## API Routes Overview

| Method | Endpoint                                    | Purpose                          |
|--------|---------------------------------------------|----------------------------------|
| POST   | `/signup-process`                           | Create a new user account        |
| POST   | `/login-process`                            | Log in (starts a session)        |
| GET    | `/logout`                                   | Clear session                    |
| GET    | `/api/songs`                                | Search & filter songs            |
| GET    | `/api/gethistory`                           | Get current user's listen history|
| POST   | `/api/addhistory`                           | Record a play                    |
| GET    | `/api/playlists`                            | List user's playlists            |
| POST   | `/api/playlists`                            | Create a playlist                |
| DELETE | `/api/playlists/<id>`                       | Delete a playlist                |
| GET    | `/api/playlists/<id>/songs`                 | List songs in a playlist         |
| POST   | `/api/playlists/<id>/songs`                 | Add a song to a playlist         |
| DELETE | `/api/playlists/<id>/songs/<song_id>`       | Remove a song from a playlist    |
| GET    | `/api/following`                            | List users the current user follows |
| POST   | `/api/following`                            | Follow a user                    |
| DELETE | `/api/following/<followed_id>`              | Unfollow a user                  |
| GET    | `/api/users/search`                         | Search users by username         |
| POST   | `/api/ratings/song`                         | Rate a song (1–5)                |
| POST   | `/api/upload`                               | Publish a new song               |

All endpoints under `/api/` require an active session and return JSON. SQL queries are parameterised through `psycopg2` to prevent SQL injection.

## Submission

Course: CSE 412 — Database Management, Spring 2026
Phase: 03 (Frontend application + database connectivity)