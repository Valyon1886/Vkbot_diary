CREATE DATABASE STORAGE;
use STORAGE;
CREATE TABLE Week(
    idWeek int,
    Even bool,
    day_id int
);

CREATE table Days(
	day_id int,
	Day_of_week LINESTRING,
	id_Schedule int
);

CREATE TABLE Schedule(
    id_Schedule int,
    Time_lesson time,
    Subject LINESTRING,
    Teacher LINESTRING,
    class_number LINESTRING,
	link LINESTRING
);

CREATE table Users(
	user_id LINESTRING,
	Group LINESTRING
);

CREATE table Users_notes(
	user_id int,
	Data datetime,
	Time_lesson time,
	Note LINESTRING
);