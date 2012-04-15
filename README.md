# smskrupp

A project using [gammu](https://github.com/gammu/gammu) to handle sms lists.

## Setup

Dependencies: sqlite3, gammu-smsd, python-gammu

On debian:

    apt-get install gammu-smsd python-gammu sqlite3 libdbi-dev libsqlite3-dev libdbd-sqlite3

Setting up the db:

    $ sqlite3 smskrupp.db < sql/*.sql

## Usage

use smskrupp command to manage groups:

    $ smskrupp add-group test
    $ smskrupp add-member 0731234567 member1 test
    $ smskrupp add-member 0731234568 member2 test
    $ smskrupp set-sender 0731234567 test phone1
    $ smskrupp list-members test

Now if you have gammu-smsd setup correctly you should be able to send a message from 0731234567 to the phone you've setup with gammu and it will deliver to all members in the group.
