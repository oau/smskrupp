#!/usr/bin/env python
import sys

import core

def usage():
    print("%s add-group <name>"%sys.argv[0])
    print("%s list-groups"%sys.argv[0])
    print("%s add-member <number> <alias> <group>"%sys.argv[0])
    print("%s set-sender <number> <group> <phone> [keyword]"%sys.argv[0])
    print("%s set-admin <number> <group> <phone> [keyword]"%sys.argv[0])
    print("%s list-members <group>"%sys.argv[0])
    print("%s fake-incoming <src> <phone> <msg>"%sys.argv[0])
    sys.exit(1)

if len(sys.argv) < 2:
    usage()

data = core.Data()

if sys.argv[1] == 'add-group':
    if len(sys.argv) != 3:
        usage()
    data.add_group(sys.argv[2])
elif sys.argv[1] == 'list-groups':
    for i,name in data.get_groups():
        print name
elif sys.argv[1] == 'list-members':
    if len(sys.argv) != 3:
        usage()
    gid = data.get_group_id(sys.argv[2])
    if not gid:
        print "no such group!"
        sys.exit(1)
    for member in data.get_group_members(gid):
        if member['sender']: s = 's'
        else: s = ' '
        if member['admin']: s = 'a'+s
        else: s = ' '+s
        s += ' %s [%s]'%(member['alias'],member['number'])
        print(s)
elif sys.argv[1] == 'add-member':
    if len(sys.argv) != 5:
        usage()
    number,alias,group = sys.argv[2:]
    number = core.normalize_number(number)
    if not number:
        print "number error!"
        sys.exit(1)
    group_id = data.get_group_id(group)
    if not group_id:
        print "group error!"
        sys.exit(1)
    data.add_number(number, alias, group_id)
elif sys.argv[1] == 'set-sender':
    if len(sys.argv) != 5 and len(sys.argv) != 6:
        usage()

    number,group,phone = sys.argv[2:5]
    number = core.normalize_number(number)
    keyword = sys.argv[5] if len(sys.argv) == 6 else ""
    group_id = data.get_group_id(group)
    if not group_id:
        print "group error!"
        sys.exit(1)
    mid = data.get_member_id(number, group_id);
    if not mid:
        print "no such number!"
        sys.exit(1)
    data.set_sender(phone, member_id=mid, keyword=keyword)
elif sys.argv[1] == 'set-admin':
    if len(sys.argv) != 5 and len(sys.argv) != 6:
        usage()

    number,group,phone = sys.argv[2:5]
    number = core.normalize_number(number)
    keyword = sys.argv[5] if len(sys.argv) == 6 else ""
    group_id = data.get_group_id(group)
    if not group_id:
        print "group error!"
        sys.exit(1)
    mid = data.get_member_id(number, group_id);
    if not mid:
        print "no such number!"
        sys.exit(1)
    data.set_admin(phone, member_id=mid, keyword=keyword)
elif sys.argv[1] == 'fake-incoming':
    if len(sys.argv) != 5:
        usage()
    src,phone,msg = sys.argv[2:]
    src = core.normalize_number(src)
    if not src:
        print "number error!"
        sys.exit(1)
    data.fake_incoming(src,phone,msg)
else:
    usage()

