-- Test-only schema derived from the user-supplied reference SQL.

-- Reset through db.test_database only; this schema is for the isolated _test database.

CREATE DATABASE CollegeSportsDB_test;
USE CollegeSportsDB_test;

-- 1. PLAYER TABLE
CREATE TABLE Player (
    player_id INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    register_no VARCHAR(30) NOT NULL UNIQUE,
    department VARCHAR(100) NOT NULL,
    `year` INT NOT NULL,
    CHECK (`year` BETWEEN 1 AND 5)
);

-- 2. SPORT TABLE
CREATE TABLE Sport (
    sport_id INT AUTO_INCREMENT PRIMARY KEY,
    sport_name VARCHAR(50) NOT NULL UNIQUE,
    `type` VARCHAR(30) NOT NULL
);

-- 3. TEAM TABLE
CREATE TABLE Team (
    team_id INT AUTO_INCREMENT PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    sport_id INT NOT NULL,
    UNIQUE (team_name, sport_id),
    FOREIGN KEY (sport_id)
        REFERENCES Sport(sport_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- 4. TEAMPLAYER TABLE
CREATE TABLE TeamPlayer (
    team_id INT NOT NULL,
    player_id INT NOT NULL,
    join_date DATE NOT NULL,
    PRIMARY KEY (team_id, player_id),
    FOREIGN KEY (team_id)
        REFERENCES Team(team_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (player_id)
        REFERENCES Player(player_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- 5. TOURNAMENT TABLE
CREATE TABLE Tournament (
    tournament_id INT AUTO_INCREMENT PRIMARY KEY,
    tournament_name VARCHAR(100) NOT NULL,
    sport_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    CHECK (end_date >= start_date),
    FOREIGN KEY (sport_id)
        REFERENCES Sport(sport_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- 6. VENUE TABLE
CREATE TABLE Venue (
    venue_id INT AUTO_INCREMENT PRIMARY KEY,
    venue_name VARCHAR(100) NOT NULL UNIQUE,
    `location` VARCHAR(150) NOT NULL,
    capacity INT NOT NULL,
    CHECK (capacity > 0)
);

-- 7. MATCHES TABLE
CREATE TABLE Matches (
    match_id INT AUTO_INCREMENT PRIMARY KEY,
    tournament_id INT NOT NULL,
    team1_id INT NOT NULL,
    team2_id INT NOT NULL,
    venue_id INT NOT NULL,
    match_date DATETIME NOT NULL,
    `status` VARCHAR(20) NOT NULL DEFAULT 'Scheduled',

    CHECK (
        `status` IN (
            'Scheduled',
            'Ongoing',
            'Completed',
            'Cancelled'
        )
    ),

    FOREIGN KEY (tournament_id)
        REFERENCES Tournament(tournament_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (team1_id)
        REFERENCES Team(team_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (team2_id)
        REFERENCES Team(team_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    FOREIGN KEY (venue_id)
        REFERENCES Venue(venue_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);
-- 8. MATCHRESULT TABLE
CREATE TABLE MatchResult (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT NOT NULL UNIQUE,
    winner_id INT NULL,
    team1_score INT NOT NULL,
    team2_score INT NOT NULL,
    FOREIGN KEY (match_id)
        REFERENCES Matches(match_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    FOREIGN KEY (winner_id)
        REFERENCES Team(team_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CHECK (team1_score >= 0),
    CHECK (team2_score >= 0)
);

-- 9. APPUSER TABLE (application login)
CREATE TABLE AppUser (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'Admin',
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (role IN ('Admin', 'Viewer'))
);

-- Insert sports
INSERT INTO Sport (sport_name, `type`) VALUES
('Cricket', 'Outdoor'),
('Football', 'Outdoor'),
('Basketball', 'Indoor'),
('Volleyball', 'Indoor'),
('Badminton', 'Indoor'),
('Chess', 'Indoor'),
('Kabaddi', 'Outdoor'),
('Hockey', 'Outdoor'),
('Table Tennis', 'Indoor'),
('Athletics', 'Outdoor');

-- Insert players
INSERT INTO Player
(`name`, register_no, department, `year`) VALUES
('Arun Kumar', 'CS001', 'CSE', 2),
('Priya Sharma', 'CS002', 'CSE', 3),
('Rahul Raj', 'IT001', 'IT', 2),
('Sneha Devi', 'IT002', 'IT', 1),
('Vijay Kumar', 'EC001', 'ECE', 3),
('Anitha R', 'EC002', 'ECE', 2),
('Karthik S', 'ME001', 'Mechanical', 1),
('Divya M', 'ME002', 'Mechanical', 2),
('Sanjay P', 'CS003', 'CSE', 4),
('Meena K', 'IT003', 'IT', 3);

-- Insert teams
INSERT INTO Team (team_name, department, sport_id) VALUES
('CSE Cricket', 'CSE', 1),
('IT Cricket', 'IT', 1),
('ECE Football', 'ECE', 2),
('CSE Football', 'CSE', 2),
('IT Basketball', 'IT', 3),
('ECE Volleyball', 'ECE', 4),
('CSE Badminton', 'CSE', 5),
('IT Chess', 'IT', 6),
('ME Kabaddi', 'Mechanical', 7),
('ECE Hockey', 'ECE', 8);

-- Assign players to teams
INSERT INTO TeamPlayer (team_id, player_id, join_date) VALUES
(1, 1, '2026-01-10'),
(1, 9, '2026-01-10'),
(2, 3, '2026-01-11'),
(2, 10, '2026-01-11'),
(3, 5, '2026-01-12'),
(4, 2, '2026-01-12'),
(5, 4, '2026-01-13'),
(6, 6, '2026-01-13'),
(7, 8, '2026-01-14'),
(9, 7, '2026-01-14');

-- Insert tournaments
INSERT INTO Tournament
(tournament_name, sport_id, start_date, end_date) VALUES
('Interdepartment Cricket Cup', 1, '2026-11-01', '2026-11-07'),
('College Football Cup', 2, '2026-11-08', '2026-11-14'),
('Basketball Championship', 3, '2026-11-15', '2026-11-18'),
('Volleyball Tournament', 4, '2026-11-19', '2026-11-22'),
('Badminton Open', 5, '2026-11-23', '2026-11-25'),
('Chess Championship', 6, '2026-11-26', '2026-11-27'),
('Kabaddi Cup', 7, '2026-11-28', '2026-11-30'),
('Hockey Tournament', 8, '2026-12-01', '2026-12-05'),
('Table Tennis Open', 9, '2026-12-06', '2026-12-07'),
('Athletics Meet', 10, '2026-12-08', '2026-12-10');

-- Insert venues
INSERT INTO Venue (venue_name, `location`, capacity) VALUES
('Main Cricket Ground', 'College Ground', 500),
('Football Field', 'North Campus', 300),
('Indoor Basketball Court', 'Sports Complex', 100),
('Volleyball Court', 'Sports Complex', 80),
('Badminton Hall', 'Indoor Block', 60),
('Chess Hall', 'Academic Block', 50),
('Kabaddi Ground', 'South Campus', 200),
('Hockey Ground', 'North Campus', 250),
('Table Tennis Room', 'Indoor Block', 40),
('Athletics Stadium', 'Main Campus', 1000);

-- Schedule matches
INSERT INTO Matches
(tournament_id, team1_id, team2_id, venue_id, match_date)
VALUES
(1, 1, 2, 1, '2026-11-02 10:00:00'),
(2, 3, 4, 2, '2026-11-09 15:00:00');

-- Enter match results
INSERT INTO MatchResult
(match_id, winner_id, team1_score, team2_score)
VALUES
(1, 1, 150, 130),
(2, 3, 2, 1);

-- Mark these matches completed
UPDATE Matches
SET `status` = 'Completed'
WHERE match_id IN (1, 2);

-- Additional teams (ids 11-18)
INSERT INTO Team (team_name, department, sport_id) VALUES
('ECE Cricket', 'ECE', 1),
('IT Football', 'IT', 2),
('CSE Basketball', 'CSE', 3),
('CSE Volleyball', 'CSE', 4),
('IT Badminton', 'IT', 5),
('CSE Chess', 'CSE', 6),
('CSE Kabaddi', 'CSE', 7),
('CSE Hockey', 'CSE', 8);

-- Additional matches (ids 3-12)
INSERT INTO Matches (tournament_id, team1_id, team2_id, venue_id, match_date) VALUES
(1, 1, 11, 1, '2026-11-03 10:00:00'),
(1, 2, 11, 1, '2026-11-04 10:00:00'),
(2, 3, 12, 2, '2026-11-10 15:00:00'),
(2, 4, 12, 2, '2026-11-11 15:00:00'),
(3, 5, 13, 3, '2026-11-15 11:00:00'),
(4, 6, 14, 4, '2026-11-19 14:00:00'),
(5, 7, 15, 5, '2026-11-23 09:30:00'),
(6, 8, 16, 6, '2026-11-26 10:00:00'),
(7, 9, 17, 7, '2026-11-28 16:00:00'),
(8, 10, 18, 8, '2026-12-01 15:00:00');

-- Results for matches 3-10 (match 4 is a draw, so winner is NULL)
INSERT INTO MatchResult (match_id, winner_id, team1_score, team2_score) VALUES
(3, 1, 120, 95),
(4, NULL, 100, 100),
(5, 3, 3, 1),
(6, 12, 0, 2),
(7, 5, 62, 58),
(8, 6, 3, 1),
(9, 7, 2, 0),
(10, 16, 0, 1);

UPDATE Matches SET `status` = 'Completed' WHERE match_id BETWEEN 3 AND 10;
-- Matches 11 and 12 stay 'Scheduled' (upcoming matches)

CREATE VIEW TournamentStandings AS
SELECT
    tr.tournament_id,
    tr.tournament_name,
    tm.team_id,
    tm.team_name,

    COUNT(r.result_id) AS matches_played,

    SUM(
        CASE
            WHEN r.winner_id = tm.team_id
            THEN 1 ELSE 0
        END
    ) AS wins,

    SUM(
        CASE
            WHEN r.result_id IS NOT NULL
             AND r.winner_id IS NOT NULL
             AND r.winner_id <> tm.team_id
            THEN 1 ELSE 0
        END
    ) AS losses,

    SUM(
        CASE
            WHEN r.result_id IS NOT NULL
             AND r.winner_id IS NULL
            THEN 1 ELSE 0
        END
    ) AS draws,

    SUM(
        CASE
            WHEN r.winner_id = tm.team_id
            THEN 3
            WHEN r.result_id IS NOT NULL
             AND r.winner_id IS NULL
            THEN 1
            ELSE 0
        END
    ) AS points

FROM Tournament AS tr
JOIN Matches AS m
    ON tr.tournament_id = m.tournament_id

JOIN Team AS tm
    ON tm.team_id = m.team1_id
    OR tm.team_id = m.team2_id

LEFT JOIN MatchResult AS r
    ON r.match_id = m.match_id

WHERE m.`status` = 'Completed'

GROUP BY
    tr.tournament_id,
    tr.tournament_name,
    tm.team_id,
    tm.team_name;

DROP PROCEDURE IF EXISTS GetTeamMatches;
CREATE PROCEDURE GetTeamMatches(IN p_team_id INT)
SELECT
    m.match_id,
    tr.tournament_name,
    CASE
        WHEN m.team1_id = p_team_id THEN t2.team_name
        ELSE t1.team_name
    END AS opponent,
    v.venue_name,
    m.match_date,
    m.`status`,
    r.team1_score,
    r.team2_score
FROM Matches AS m
JOIN Tournament AS tr
    ON m.tournament_id = tr.tournament_id
JOIN Team AS t1
    ON m.team1_id = t1.team_id
JOIN Team AS t2
    ON m.team2_id = t2.team_id
JOIN Venue AS v
    ON m.venue_id = v.venue_id
LEFT JOIN MatchResult AS r
    ON m.match_id = r.match_id
WHERE m.team1_id = p_team_id
   OR m.team2_id = p_team_id
ORDER BY m.match_date;

DROP TRIGGER IF EXISTS ValidateMatchResult;
CREATE TRIGGER ValidateMatchResult
BEFORE INSERT ON MatchResult
FOR EACH ROW
SET NEW.winner_id = (
    SELECT
        CASE
            WHEN NEW.winner_id IS NULL THEN NULL
            WHEN NEW.winner_id = m.team1_id
                 AND NEW.team1_score > NEW.team2_score
                THEN NEW.winner_id
            WHEN NEW.winner_id = m.team2_id
                 AND NEW.team2_score > NEW.team1_score
                THEN NEW.winner_id
            WHEN NEW.team1_score = NEW.team2_score
                 AND NEW.winner_id IS NULL
                THEN NULL
            ELSE NULL
        END
    FROM Matches m
    WHERE m.match_id = NEW.match_id
);




