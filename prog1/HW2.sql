CREATE TABLE user (user_id INTEGER PRIMARY KEY, name, url);
CREATE TABLE question (q_id INTEGER PRIMARY KEY, title, body, ask_date, asker_id);
CREATE TABLE answer (a_id INTEGER PRIMARY KEY, q_id, body, answer_date, answerer_id);
CREATE TABLE q_tag (q_id, tag);
-- votes are 1 for upvote, -1 for downvote
-- votes really have users, but we do not have users in the data download
CREATE TABLE q_vote (q_vote_id INTEGER PRIMARY KEY, q_id, v_date, value);
CREATE TABLE a_vote (a_vote_id INTEGER PRIMARY KEY, a_id, v_date, value);


--1
SELECT title
FROM question
ORDER BY ask_date DESC
LIMIT 25;
--2
SELECT title
FROM question
JOIN q_vote USING (q_id)
GROUP BY q_id
ORDER BY SUM(value) DESC
LIMIT 25;
--3
SELECT answer.body
FROM answer
JOIN question USING (q_id)
JOIN a_vote USING (a_id)
WHERE q_id = 267
GROUP BY (a_id)
ORDER BY SUM(value) DESC;
--4
SELECT name, SUM(value) AS net_votes
FROM user
JOIN answer ON answerer_id = user_id
JOIN a_vote USING (a_id)
WHERE name = 'Donut'
GROUP BY user_id;
--5
SELECT name, a_total + q_total AS activity_total
FROM user
JOIN (SELECT SUM(value) AS a_total
      FROM user
      JOIN answer ON answerer_id = user_id
      JOIN a_vote USING (a_id)
      WHERE name = 'Donut'
      GROUP BY answerer_id)
JOIN (SELECT SUM(value) AS q_total
      FROM user
      JOIN question ON asker_id = user_id
      JOIN q_vote USING (q_id)
      WHERE name = 'Donut'
      GROUP BY asker_id)
WHERE name = 'Donut'; --random user

--6
SELECT name, SUM(value) AS net_votes
FROM user
JOIN answer ON answerer_id = user_id
JOIN a_vote USING (a_id)
GROUP BY answerer_id
ORDER BY net_votes DESC
LIMIT 50;
--7
SELECT name
FROM user
JOIN question ON asker_id = user_id
GROUP BY asker_id
HAVING COUNT(q_id) >= 3;
--8
SELECT name
FROM user
JOIN question on asker_id = user_id
JOIN q_tag USING (q_id)
WHERE tag = 'bacon';
--9
SELECT name, tag, SUM(a_vote.value) AS net_votes
FROM user
JOIN answer ON answerer_id = user_id
JOIN question USING (q_id)
JOIN a_vote USING (a_id)
JOIN q_tag USING (q_id)
WHERE name = 'Donut' --random user
GROUP BY tag;