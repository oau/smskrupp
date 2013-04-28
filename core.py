# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function

from config import config
import sqlite3
from time import strftime, localtime, mktime


def normalize_number(number):
    if number.startswith('07'):
        return '+46' + number[1:]
    elif number.startswith('0046'):
        return '+' + number[2:]
    elif number.startswith('+46'):
        return number
    return None


class Data:
    def __init__(self):
        self.conn = sqlite3.connect(config.db)
        self.cursor = self.conn.cursor()

    def setup_db(self):
        '''Creates the database tables.'''
        with open('sql/smskrupp.sql', 'r') as f:
            self.cursor.executescript(f.read())
            self.conn.commit()

    def add_number(self, number, alias, group_id):
        ''' updates alias if number already exists in group
            does nothing and returns None if alias already exists
            alias = None will generate a new unique alias
        '''
        c = self.cursor
        if alias == None:
            base = "noname"
            c.execute("select alias from qq_groupMembers " +
                      "where alias like ? order by alias ",
                      (base + '%',))
            max_num = 0
            for row in c:
                num = row[0][len(base):]
                if num.isdigit() and int(num) > max_num:
                    max_num = int(num)
            alias = base + str(max_num + 1)

        c.execute("insert or ignore into qq_groupMembers " +
                  "(number, groupId, alias) " +
                  "values (?,?,?)",
                  (number, group_id, alias))
        c.execute("update qq_groupMembers set alias=? " +
                  "where number=? and groupId=?",
                  (alias, number, group_id))
        self.conn.commit()
        return self.get_member_id(number, group_id)

    def set_member_info(self, member_id, **kwargs):
        c = self.cursor
        if 'sender' in kwargs:
            c.execute("update qq_groupMembers set sender=? where id=?",
                    (kwargs['sender'], member_id))
        if 'admin' in kwargs:
            c.execute("update qq_groupMembers set admin=? where id=?",
                    (kwargs['admin'], member_id))
        if 'alias' in kwargs:
            c.execute("update qq_groupMembers set alias=? where id=?",
                    (kwargs['alias'], member_id))
        self.conn.commit()

    def remove_number(self, member_id=None, number=None, group_id=None):
        if not member_id:
            member_id = self.get_member_id(number, group_id)
        if member_id:
            c = self.cursor
            c.execute("delete from qq_groupMembers where id=?",
                      (member_id,))
            self.conn.commit()

    def add_group(self, name, keyword, monthLimit=-1):
        ''' create a group and return id of the created group
        '''
        c = self.cursor
        c.execute("insert into qq_groups (name,keyword, monthLimit) " +
                  "values (?,?,?)",
                  (name, keyword, monthLimit))
        self.conn.commit()
        c.execute('select id from qq_groups where name=?', (name,))
        group_id = None
        for row in c:
            group_id = row[0]
        return group_id

    def set_group_month_limit(self, group_id, monthLimit):
        c = self.cursor
        c.execute("update qq_groups set monthLimit=? where id=?",
                (monthLimit, group_id))
        self.conn.commit()

    def remove_group(self, gid):
        ''' completely remove a group and all it's members
        '''
        c = self.cursor
        c.execute("delete from qq_groupMembers where groupId=?",
                  (gid,))
        c.execute("delete from qq_webUserGroups where groupId=?",
                  (gid,))
        c.execute("delete from qq_groups where id=?",
                  (gid,))
        self.conn.commit()

    def get_group_senders(self, group_id):
        c = self.cursor
        c.execute('select id, number, alias from qq_groupMembers ' +
                  'where groupId=? and sender=1', (group_id,))
        return [{'id': row[0], 'number': row[1], 'alias': row[2]} for row in c]

    def get_group_admins(self, group_id):
        c = self.cursor
        c.execute('select id,number,alias from qq_groupMembers ' +
                  'where groupId=? and admin=1', (group_id,))
        return [{'id': row[0], 'number': row[1], 'alias': row[2]} for row in c]

    def get_group_members(self, group_id):
        ''' return array of dicts describing members (id, number, alias, sender, admin)
        '''
        c = self.cursor
        c.execute('select id,number,alias,sender,admin from qq_groupMembers '+
                'where groupId=?',
                (group_id, ))
        return [{'id': row[0], 'number': row[1], 'alias': row[2], 'sender': (row[3] ==1 ),
            'admin':(row[4]==1)} for row in c]

    def get_groups(self, number=None):
        ''' returns array of dicts describing groups (id, name keyword) containing number
        '''
        c = self.cursor
        if number:
            c.execute('select g.id, g.name, g.keyword, g.monthLimit from qq_groupMembers m '
                    + 'join qq_groups g on g.id = m.groupId '
                    + 'where m.number=? order by g.name asc',
                    (number,))
        else:
            c.execute('select id,name,keyword,monthLimit from qq_groups order by name asc')
        return [{'id':row[0], 'name':row[1], 'keyword':row[2], 'month_limit':row[3]} for row in c]

    def get_send_groups(self, sender):
        ''' returns array of dicts describing groups (id, name keyword, monthLimit) where the sender can send
        '''
        c = self.cursor
        c.execute('select g.id, g.name, g.keyword, g.monthLimit from qq_groupMembers m '
                + 'join qq_groups g on g.id = m.groupId '
                + 'where m.number=? and m.sender=1 order by g.name asc',
                (sender,))
        return [{'id':row[0], 'name':row[1], 'keyword':row[2], 'month_limit':row[3]} for row in c]

    def get_admin_groups(self, sender):
        ''' returns array of dicts describing groups (id, name keyword, month_limit) where the sender can admin
        '''
        c = self.cursor
        c.execute('select g.id, g.name, g.keyword, g.monthLimit from qq_groupMembers m '
                + 'join qq_groups g on g.id = m.groupId '
                + 'where m.number=? and m.admin=1 order by g.name asc',
                (sender,))
        return [{'id':row[0], 'name':row[1], 'keyword':row[2], 'month_limit':row[3]} for row in c]

    def get_group_id(self, name):
        info = self.get_group_info(name=name)
        if not info:
            return None
        return info['id']

    def get_group_info(self, group_id=None, name=None):
        c = self.cursor
        if group_id:
            c.execute('select id,name,keyword,monthLimit from qq_groups where id=?', (group_id,))
        elif name:
            c.execute('select id,name,keyword,monthLimit from qq_groups where name=?', (name,))
        else:
            return None
        x = c.fetchone()
        if not x:
            return None
        return {'id':x[0], 'name':x[1], 'keyword':x[2], 'month_limit':x[3]}

    def get_member_id(self, number, group_id):
        c = self.cursor
        c.execute('select id from qq_groupMembers where groupId=? and number=?',
                (group_id, number))
        x = c.fetchone()
        if not x:
            return None
        return x[0]

    def get_member_ids(self, number):
        ''' get member ids for number in any group
        '''
        c = self.cursor
        c.execute('select id from qq_groupMembers where number=?',
                (number,))
        ret = []
        for row in c:
            ret.append(row[0])
        return ret

    def get_member_info(self, member_id):
        c = self.cursor
        c.execute('select m.id,m.number,m.alias,m.groupId,g.name from qq_groupMembers m '
                + 'left join qq_groups g on g.id = m.groupId where m.id=?',
                (member_id,))
        x = c.fetchone()
        if x:
            return {'id': x[0], 'number': x[1], 'alias': x[2], 'groupId': x[3], 'groupName': x[4]}
        return None

    def _calculate_udh_part(self, udh):
        if not udh:
            return None
        length = int(udh[:2], 16)
        i = 1
        while i <= length:
            # parse one IEI
            iei_id = int(udh[i * 2: i * 2 + 2], 16)
            i += 1
            iei_len = int(udh[i * 2: i * 2 + 2], 16)
            if not iei_id == 0:
                # not concatenation iei
                i += iei_len
                continue
            i += 1
            ref = int(udh[i * 2: i * 2 + 2], 16)
            i += 1
            num_parts = int(udh[i * 2: i * 2 + 2], 16)
            i += 1
            part = int(udh[i * 2: i * 2 + 2], 16)
            return part, num_parts, ref

    def get_unprocessed(self):
        c = self.cursor
        c.execute("select ID,SenderNumber,RecipientID,TextDecoded,UDH " +
                  "from inbox where Processed='false'")
        parts = {}
        ret = []
        for row in c:
            i, src, phone, text, udh = row
            x = self._calculate_udh_part(udh)
            if x:
                part, num_parts, ref = x
                key = src + '-' + str(ref)
                if not key in parts:
                    parts[key] = src, phone, [], []
                parts[key][2].append((part, text))
                parts[key][3].append(i)

                if len(parts[key][2]) == num_parts:
                    # found all parts
                    tot_text = "".join(map(lambda x: x[1], sorted(parts[key][2], key=lambda x: x[0])))
                    ret.append({'ids': parts[key][3], 'src': src, 'phone': phone, 'text': tot_text})
                    del parts[key]
            else:
                # single part
                ret.append({'ids': [i], 'src': src, 'phone': phone, 'text': text})
        return ret

    def set_processed(self, msgId, status='true'):
        c = self.cursor
        c.execute("update inbox set Processed=? where ID=?", (status, msgId))
        self.conn.commit()

    def fake_incoming(self, src, phoneId, msg):
        c = self.cursor
        c.execute("insert into inbox (RecipientID,SenderNumber,TextDecoded,Text,UDH) "
                  "values (?,?,?,?,?)", (phoneId, src, msg, "00", "00"))
        self.conn.commit()

    def purge_all_data(self):
        c = self.cursor
        c.execute('delete from qq_groupMembers')
        c.execute('delete from qq_groups')
        c.execute('delete from inbox')
        c.execute('delete from outbox')
        c.execute('delete from sentitems')
        self.conn.commit()

    def cleanup(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None

    def add_webuser(self, username, pw, privilege):
        import bcrypt
        c = self.cursor
        h = bcrypt.hashpw(pw, bcrypt.gensalt())
        c.execute('insert into qq_webUsers (username,hash,privilege) values (?,?,?)',
                (username, h, privilege))
        self.conn.commit()

    def get_webusers(self):
        c = self.cursor
        c.execute('select u.id,u.username,u.privilege,g.id,g.name from qq_webUsers u '
                + 'left join qq_webUserGroups wg on wg.userId = u.id '
                + 'left join qq_groups g on g.id = wg.groupId '
                + 'order by u.id')
        ret = []
        seen = []
        for row in c:
            if row[0] in seen:
                ret[-1]['groups'].append({'group_id': row[3], 'group_name': row[4]})
            else:
                seen.append(row[0])
                ret.append({'user_id': row[0], 'username': row[1], 'privilege': row[2], 'groups': []})
                if row[3]:
                    ret[-1]['groups'].append({'group_id': row[3], 'group_name': row[4]})

        return ret

    def get_webuser_groups(self, webuser_id):
        c = self.cursor
        c.execute('select groupId,name,keyword from qq_webUserGroups wg '
            + 'left join qq_groups g on g.id=wg.groupId where userId=?',
                (webuser_id,))
        return [{'id': row[0], 'name': row[1], 'keyword': row[2]} for row in c]

    def set_webuser_group(self, webuser_id, group_id):
        c = self.cursor
        c.execute('insert or ignore into qq_webUserGroups (userId,groupId) values (?,?)',
                (webuser_id, group_id))
        self.conn.commit()

    def remove_webuser(self, webuser_id):
        c = self.cursor
        c.execute('delete from qq_webUserGroups where userId=?',
                (webuser_id,))
        c.execute('delete from qq_webUsers where id=?',
                (webuser_id,))
        self.conn.commit()

    def remove_webuser_group(self, webuser_id, group_id):
        c = self.cursor
        c.execute('delete from qq_webUserGroups where userId=? and groupId=?',
                (webuser_id, group_id))
        self.conn.commit()

    def set_webuser_pw(self, user_id, pw):
        import bcrypt
        h = bcrypt.hashpw(pw, bcrypt.gensalt())
        c = self.cursor
        c.execute('update qq_webUsers set hash=? where id=?',
                (h, user_id))
        self.conn.commit()

    def check_webuser_login(self, username, password):
        c = self.cursor
        c.execute('select username,hash,privilege,id from qq_webUsers where username=?',
                (username,))
        row = c.fetchone()
        if row:
            import bcrypt
            hashed = row[1]
            if bcrypt.hashpw(password, hashed) == hashed:
                return row[3], row[2]
        return 0, 0


    def increment_sent_stats(self, group_id, cnt=1):
        ''' update statistics table
        '''
        day = strftime("%Y-%m-%d %H:%M:%S", localtime())
        c = self.cursor
        c.execute("insert or ignore into qq_groupStatistics "+
                  "(day, groupId, cnt) "+
                  "values (?,?,0)",
                  (day, group_id))
        c.execute("update qq_groupStatistics "+
                  "set cnt=cnt+? "
                  "where day=? and groupId=?",
                  (cnt, day, group_id))
        self.conn.commit()

    def get_number_of_messages(self, group_id, days):
        ''' count the number of massages for this group over the last <days> days
        '''
        day = strftime("%Y-%m-%d %H:%M:%S", localtime(mktime(localtime()) - 3600*24*days))
        c = self.cursor
        c.execute("select sum(cnt) from qq_groupStatistics "+
                  "where groupId=? and day >= ?", (group_id,day))
        row = c.fetchone()
        if not row[0]: return 0
        return row[0]



class Doer:
    def __init__(self, sender):
        self.data = Data()
        self.sender = sender

    def cleanup(self):
        self.data.cleanup()

    def _log(self, text):
        with open(config.log, "a") as log:
            t = strftime("%Y-%m-%d %H:%M:%S", localtime())
            log.write("[%s] [doer] %s\n" % (t, text.encode('utf-8')))

    def _parse_action(self, src, orig_msg):
        groups = self.data.get_groups(number=src)
        send_groups = self.data.get_send_groups(src)
        lmsg = orig_msg.lower().strip()
        if lmsg == 'stop' or lmsg == 'stopp':
            return {'action': 'stop', 'groups': groups}
        if lmsg.startswith(config.admin_prefix):
            admin_cmd = lmsg[len(config.admin_prefix):]
            first_word = admin_cmd.split(" ")[0]
            group = None

            # check if we have keyword
            for g in groups:
                if first_word == g['keyword']:
                    admin_cmd = admin_cmd[len(first_word):].strip()
                    group = g
                    break

            if not group:
                # no keyword
                if len(groups) == 1 and admin_cmd in ["stop", "stopp"]:
                    return {'action': 'stop', 'groups': groups}

                if len(send_groups) == 1:
                    group = send_groups[0]

            if not group:
                # can't figure out group, give up
                return {'action': 'invalid'}

            if admin_cmd in ["stop", "stopp"]:
                return {'action': 'stop', 'groups': groups}

            number = None
            action = None
            if admin_cmd.startswith('add '):
                rest = admin_cmd[len('add '):].strip()
                if rest.startswith('sender '):
                    action = 'add_sender'
                    number = normalize_number(rest[len('sender '):].strip())
                elif rest.startswith('admin '):
                    action = 'add_admin'
                    number = normalize_number(rest[len('admin '):].strip())
                else:
                    action = 'add'
                    number = normalize_number(rest)
            if action and number:
                return {'action': action, 'number': number, 'group': group}
            else:
                return {'action': 'invalid'}

        if lmsg.startswith(config.send_prefix):
            send_msg = None
            send_cmd = orig_msg[len(config.send_prefix):]
            lfirst_word = send_cmd.split(" ")[0].lower()
            for g in groups:
                if lfirst_word == g['keyword'].lower():
                    send_msg = "%s%s %s" % (config.send_prefix, g['keyword'],
                            send_cmd[len(lfirst_word):].strip())
                    group = g
                    break
            if send_msg and group:
                return {'action': 'sendout', 'group': group, 'msg': send_msg}

        return {'action': 'invalid'}

    def sendout(self, group_id, msg):
        group = self.data.get_group_info(group_id=group_id)
        self._log("doing sendout to group %s" % group['name'])
        members = self.data.get_group_members(group['id'])
        for member in members:
            cnt = self.sender.send(member['number'], msg)
            self.data.increment_sent_stats(group['id'], cnt)

    def _handle_message(self, ids, src, phone, orig_msg):
        self._log("got message '%s' from %s to %s" % (orig_msg, src, phone))
        action = self._parse_action(src, orig_msg)

        status = 'invalid'
        if action['action'] == 'stop':
            for g in action['groups']:
                self.data.remove_number(number=src, group_id=g['id'])
            status = 'stop'
        elif action['action'] == 'sendout':
            group = action['group']
            msg = action['msg']
            if not src in [m['number'] for m in self.data.get_group_senders(group['id'])]:
                self._log("Warning: Unauthorized sendout command '%s' from %s to %s" %
                        (orig_msg, src, phone))
                status = 'unauthorized'
            elif group['month_limit'] >= 0 and self.data.get_number_of_messages(group['id'], 30) >= group['month_limit']:
                self._log("Warning: limit %d reached for group '%s'" % (group['month_limit'], group['name']))
                status = 'limited'
            else:
                self.sendout(group['id'], msg)
                status = 'send'
        elif action['action'] in ['add', 'add_sender', 'add_admin']:
            group = action['group']
            if not src in [m['number'] for m in self.data.get_group_admins(group['id'])]:
                self._log("Warning: Unauthorized admin command '%s' from %s to %s" % (orig_msg, src, phone))
                status = 'unauthorized'
            else:
                status = 'admin'
                self._log("doing command '%s' to group %s" % (action['action'], group['name']))
                mid = self.data.add_number(action['number'], None, group['id'])
                is_sender, is_admin = False, False
                if action['action'] == 'add_sender':
                    self.data.set_member_info(mid, sender=True)
                    is_sender = True
                elif action['action'] == 'add_admin':
                    self.data.set_member_info(mid, sender=True, admin=True)
                    is_sender, is_admin = True, True

                user_groups = self.data.get_groups(number=action['number'])
                user_send_groups = self.data.get_send_groups(action['number'])
                welcomes = Helper().get_welcomes(group['name'], group['keyword'], is_sender, is_admin, user_groups, user_send_groups)
                for msg in welcomes:
                    self.sender.send(action['number'], msg)
        elif action['action'] == 'invalid':
            # send help message
            user_groups = self.data.get_groups(number=src)
            user_send_groups = self.data.get_send_groups(src)
            user_admin_groups = self.data.get_admin_groups(src)
            helps = Helper().get_help(user_groups, user_send_groups, user_admin_groups)
            for msg in helps:
                self.sender.send(src, msg)

        for i in ids:
            self.data.set_processed(i, status)

    def run(self):
        self._log("starting doer")
        messages = self.data.get_unprocessed()
        for m in messages:
            self._handle_message(m['ids'], m['src'], m['phone'], m['text'])
        self.cleanup()


class Sender:
    def __init__(self):
        from gammu import smsd
        self.smsd = smsd.SMSD(config.smsdrc)

    def _log(self, text):
        with open(config.log, "a") as log:
            t = strftime("%Y-%m-%d %H:%M:%S", localtime())
            log.write("[%s] [doer] %s\n" % (t, text.encode('utf-8')))

    def send(self, dest, msg):
        ''' return number of messages sent
        '''
        # this length calculation will fail will not work for some special
        # gsm7 chars like [
        if len(msg) <= 160:
            message = {'Text': msg, 'SMSC': {'Location': 1}, 'Number': dest}
            self._log("sending single part message " + str(message))
            self.smsd.InjectSMS([message])
            return 1
        else:
            # multipart
            self._log("sending multipart message")
            smsinfo = {
                    'Class': 1,
                    'Unicode': False,
                    'Entries':  [{
                            'ID': 'ConcatenatedTextLong',
                            'Buffer': msg
                        }]}
            # Encode messages
            from gammu import EncodeSMS
            encoded = EncodeSMS(smsinfo)
            # Send messages
            for message in encoded:
                # Fill in numbers
                message['SMSC'] = {'Location': 1}
                message['Number'] = dest
                # Actually send the message
                self._log("sending part of message: " + str(message))
                self.smsd.InjectSMS([message])
            return len(encoded)


class Helper:
    def get_welcomes(self, group_name, group_kw, is_sender, is_admin, groups, send_groups):
        msg = u"Välkommen till smslistan %s.\n" % group_name
        if len(groups) == 1:
            msg += u"För att lämna listan skriv ett sms med texten \"stop\"."
        else:
            msg += u"För att lämna listan skriv ett sms med texten \"%s%s stop\"." % (
                   config.admin_prefix, group_kw)
        if is_sender:
            msg += u"\nFör att skicka ett sms, börja smset med %s%s." % (config.send_prefix, group_kw)
        if is_admin:
            msg += u"\nFör att lägga till någon till listan, skicka \"%s%s add [nummer]\"" % (config.admin_prefix, group_kw)
        return [msg]

    def get_help(self, groups, send_groups, admin_groups):
        msgs = []
        send_names = [x['name'] for x in send_groups]
        admin_names = [x['name'] for x in admin_groups]
        for g in groups:
            msg = u"Det här är den automatiska smslistan %s.\n" % g['name']
            if len(groups) == 1:
                msg += u"För att lämna listan skriv ett sms med texten \"stop\"."
            else:
                msg += u"För att lämna listan skriv ett sms med texten \"%s%s stop\"." % (
                   config.admin_prefix, g['keyword'])
            if g['name'] in send_names:
                msg += u"\nFör att skicka ett sms, börja smset med %s%s." % (config.send_prefix, g['keyword'])
            if g['name'] in admin_names:
                msg += u"\nFör att lägga till någon till listan, skicka \"%s%s add [nummer]\"" % (config.admin_prefix, g['keyword'])

            msgs.append(msg)
        return msgs
