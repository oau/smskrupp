DROP TABLE IF EXISTS qq_groupMembers;
CREATE TABLE qq_groupMembers (
id integer primary key autoincrement,
number varchar(22) not null,
groupId integer not null,
alias varchar(50) not null,
sender boolean not null default 0,
admin boolean not null default 0,
unique (number, groupId),
unique (alias, groupId));

DROP TABLE IF EXISTS qq_groups;
CREATE TABLE qq_groups (
id integer primary key autoincrement,
name varchar(50) not null,
keyword varchar(10) not null,
monthLimit integer not null default -1,
unique (name),
unique (keyword));

DROP TABLE IF EXISTS qq_webUsers;
CREATE TABLE qq_webUsers (
id integer primary key autoincrement,
username varchar(32) not null,
hash char(60) not null,
privilege integer not null,
unique (username));

DROP TABLE IF EXISTS qq_webUserGroups;
CREATE TABLE qq_webUserGroups (
userId integer not null,
groupId integer not null,
unique (userId,groupId));

DROP TABLE IF EXISTS qq_groupStatistics;
CREATE TABLE qq_groupStatistics (
id integer primary key autoincrement,
groupId integer not null,
day datetime not null,
cnt integer not null,
unique (groupId,day));
