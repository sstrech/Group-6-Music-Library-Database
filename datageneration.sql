-- Users:
INSERT INTO Users (u_Username, u_PasswordHash, u_FirstName, u_LastName, u_Email)
SELECT 
    'Username_' || i,                                  
    '$2a$12$35FP5XlOL7gDck3drfpUY.XX0bosmtmpLplRDrjUUnf5.ex6P2BRO',
    'First',                                        
    'Last',                                      
    'person' || i || '@gmail.com'            
FROM generate_series(1, 500) AS i;

-- Admins:
INSERT INTO Admins (a_UserID)
SELECT u_UserID 
FROM Users 
ORDER BY RANDOM() 
LIMIT 5;

-- Artists:
INSERT INTO Artists (art_UserID)
SELECT u_UserID 
FROM Users 
ORDER BY RANDOM() 
LIMIT 100;

-- Genres:
INSERT INTO Genres (g_Name) VALUES ('Jazz'), ('Classical'), ('Electronic'), ('Reggae'), ('Indie'), ('Metal'), ('Folk'), ('Blues'), ('Soul'), ('Pop'), ('Rock'), ('Hip Hop'), ('R&B'), ('Country'),
('Punk'), ('Alternative'), ('Disco'), ('Funk'), ('Gospel'), ('House'), ('Techno'), ('Trance'), ('K-Pop'), 
('Latin'), ('Reggaeton'), ('Ska'), ('Grunge'), ('Ambient'), ('Lo-Fi'), ('Afrobeats');

-- Albums:
INSERT INTO Albums (al_releasedate, al_artistID, al_genreID, al_name)
SELECT
	CURRENT_DATE - (random()*365*5)::int,
	(SELECT art_artistID FROM Artists WHERE art_artistID > (i*0) ORDER BY RANDOM() LIMIT 1),
	(SELECT g_genreID FROM Genres WHERE g_genreID > (i*0) ORDER BY RANDOM() LIMIT 1),
	'Album Name #' || i
FROM generate_series(1, 500) AS i;

-- Playlists:
INSERT INTO Playlists (pl_name, pl_createdAt, pl_userID)
SELECT
	'Playlist Name #' || i,
	CURRENT_DATE - (random()*365*4)::int,
	(SELECT u_userID FROM Users WHERE u_userID > (i*0) ORDER BY RANDOM() LIMIT 1)
FROM generate_series(1, 500) AS i;

-- Songs:
INSERT INTO songs (s_name, s_length, s_releasedate, s_artistID, s_genreID)
SELECT
	'Song Name #' || i,
	FLOOR(100+ random()*300)::int,
	CURRENT_DATE - (random()*365*5)::int,
	(SELECT art_artistID FROM Artists WHERE art_artistID > (i*0) ORDER BY RANDOM() LIMIT 1),
	(SELECT g_genreID FROM Genres WHERE g_genreID > (i*0) ORDER BY RANDOM() LIMIT 1)
FROM generate_series(1, 500) AS i;

-- Follows:
WITH NotSamePair AS (
	SELECT
		(SELECT u_userID FROM Users WHERE u_userID > (i*0) ORDER BY RANDOM() LIMIT 1) AS follower,
		(SELECT u_userID FROM Users WHERE u_userID > (i*0) ORDER BY RANDOM() LIMIT 1) AS followed,
		CURRENT_DATE - (random()*365*5)::int AS createdAt
	FROM generate_series(1, 1300) AS i
)

INSERT INTO Follows (f_followerID, f_followedID, f_createdAt)
SELECT
	NotSamePair.follower,
	NotSamePair.followed,
	NotSamePair.createdAt
FROM NotSamePair
WHERE NotSamePair.follower != NotSamePair.followed
ON CONFLICT DO NOTHING;

-- SongRatings:
WITH NotSamePair AS (
	SELECT
		FLOOR(1+random()*5)::int AS rating,
		CURRENT_DATE - (random()*365*1)::int AS createDate,
		(SELECT u_userID FROM Users WHERE u_userID > (i*0) ORDER BY RANDOM() LIMIT 1) AS userID,
		(SELECT s_songID FROM Songs WHERE s_songID > (i*0) ORDER BY RANDOM() LIMIT 1) AS songID
		
	FROM generate_series(1, 3100) AS i
)

INSERT INTO songratings (sr_rating, sr_createdate, sr_userid, sr_songid)
SELECT
	NotSamePair.rating,
	NotSamePair.createDate,
	NotSamePair.userID,
	NotSamePair.songID
FROM NotSamePair

ON CONFLICT DO NOTHING;

-- AlbumRatings:
WITH NotSamePair AS (
	SELECT
		FLOOR(1+random()*5)::int AS rating,
		CURRENT_DATE - (random()*365*1)::int AS createDate,
		(SELECT u_userID FROM Users WHERE u_userID > (i*0) ORDER BY RANDOM() LIMIT 1) AS userID,
		(SELECT al_albumID FROM Albums WHERE al_albumID > (i*0) ORDER BY RANDOM() LIMIT 1) AS albumID
		
	FROM generate_series(1, 2100) AS i
)

INSERT INTO albumratings (ar_rating, ar_createdate, ar_userid, ar_albumid)
SELECT
	NotSamePair.rating,
	NotSamePair.createDate,
	NotSamePair.userID,
	NotSamePair.albumID
FROM NotSamePair

ON CONFLICT DO NOTHING;

-- ListenHistory:
WITH NotSamePair AS (
	SELECT
		FLOOR(1+random()*9000)::int AS listenedTime,
		(SELECT u_userID FROM Users WHERE u_userID > (i*0) ORDER BY RANDOM() LIMIT 1) AS userID,
		(SELECT s_songID FROM Songs WHERE s_songID > (i*0) ORDER BY RANDOM() LIMIT 1) AS songID
		
	FROM generate_series(1, 2100) AS i
)

INSERT INTO listenHistory (lr_listenedTime, lr_userID, lr_songid)
SELECT
	NotSamePair.listenedTime,
	NotSamePair.userID,
	NotSamePair.songID
FROM NotSamePair

ON CONFLICT (lr_userID, lr_songID) DO NOTHING;

-- AlbumSongs
INSERT INTO AlbumSongs (als_AlbumID, als_SongID)
SELECT
	a.al_AlbumID,
	s.s_SongID
FROM
	(SELECT al_AlbumID FROM Albums ORDER BY RANDOM() LIMIT 1500) a,
	(SELECT s_SongID FROM Songs ORDER BY RANDOM() LIMIT 3) s
ON CONFLICT DO NOTHING;

-- PlaylistSongs
INSERT INTO PlaylistSongs (ps_PlaylistID, ps_SongID)
SELECT
	p.pl_PlaylistID,
	s.s_SongID
FROM
	(SELECT pl_PlaylistID FROM Playlists ORDER BY RANDOM() LIMIT 1500) p,
	(SELECT s_SongID FROM Songs ORDER BY RANDOM() LIMIT 3) s
ON CONFLICT DO NOTHING;
