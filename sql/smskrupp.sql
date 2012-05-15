DROP TABLE IF EXISTS qq_adminmap;
CREATE TABLE qq_adminmap (
id integer primary key autoincrement, 
memberId integer not null,
dest varchar(22) not null, 
keyword varchar(32) not null);

DROP TABLE IF EXISTS qq_groupMembers;
CREATE TABLE qq_groupMembers (
id integer primary key autoincrement,
number varchar(22),
groupId integer not null,
alias varchar(50),
unique (number, groupId));

DROP TABLE IF EXISTS qq_groups;
CREATE TABLE qq_groups (
id integer primary key autoincrement,
name varchar(50));

DROP TABLE IF EXISTS qq_sendmap;
CREATE TABLE qq_sendmap (
id integer primary key autoincrement, 
memberId not null,
dest varchar(22) not null, 
keyword varchar(32) not null);
