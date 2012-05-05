from config import config
import sqlite3
import gammu.smsd
from time import strftime, localtime

def normalize_number(number):
    if number.startswith('07'):
        return '+46'+number[1:]
    elif number.startswith('0046'):
        return '+'+number[2:]
    elif number.startswith('+46'):
        return number
    return None

class Data:
    def __init__(self):
        self.conn = sqlite3.connect(config.db)
        self.cursor = self.conn.cursor()

    def setup_db(self):
        c = self.cursor
        c.execute("CREATE TABLE IF NOT EXISTS qq_groups "+
                  "(id integer primary key autoincrement, name varchar(50))")
        c.execute("CREATE TABLE IF NOT EXISTS qq_groupMembers "+
                  "(id integer primary key autoincrement, number varchar(22),"+
                  "groupId integer not null, alias varchar(50))")
        c.execute("CREATE TABLE IF NOT EXISTS qq_sendmap "+
                  "(id integer primary key autoincrement, "+
                  "memberId not null, dest varchar(22) not null, "+
                  "keyword varchar(32) not null)")
        c.execute("CREATE TABLE IF NOT EXISTS qq_adminmap "+
                  "(id integer primary key autoincrement, "+
                  "memberId integer not null, dest varchar(22) not null, "+
                  "keyword varchar(32) not null)")
        self.conn.commit()

    def add_number(self, number, alias, group_id):
        ''' updates alias if number already exists in group
        '''
        c = self.cursor
        c.execute("insert or ignore into qq_groupMembers "+
                  "(number, groupId, alias) "+
                  "values (?,?,?)",
                  (number, group_id, alias))
        c.execute("update qq_groupMembers set alias=? "+
                  "where number=? and groupId=?",
                  (alias, number, group_id))
        self.conn.commit()
        return self.get_member_id(number,group_id)

    #def add_sender(self, number, dest, keyword=""):
    def set_sender(self, dest, keyword="", member_id=None, number=None, group_id=None):
        ''' requires either member_id or number+group_id
        '''
        if not member_id:
            if number and group_id:
                member_id = self.get_member_id(number, group_id)
            else:
                raise TypeError("Didn't get the required kw params")

        if member_id:
            c = self.cursor
            c.execute("insert into qq_sendmap (memberId,dest,keyword) "+
                      "values (?,?,?)",
                      (member_id, dest, keyword))
            self.conn.commit()

    def set_admin(self, dest, keyword="", member_id=None, number=None, group_id=None):
        ''' requires either member_id or number+group_id
        '''
        if not member_id:
            if number and group_id:
                member_id = self.get_member_id(number, group_id)
            else:
                raise TypeError("Didn't get the required kw params")

        if member_id:
            c = self.cursor
            c.execute("insert into qq_adminmap (memberId,dest,keyword) "+
                      "values (?,?,?)",
                      (member_id, dest, keyword))
            self.conn.commit()

    def remove_number(self, member_id=None, number=None, group_id=None):
        if not member_id:
            member_id = self.get_member_id(number, group_id)
        if member_id:
            c = self.cursor
            c.execute("delete from qq_sendmap where memberId=?",
                      (member_id,))
            c.execute("delete from qq_adminmap where memberId=?",
                      (member_id,))
            c.execute("delete from qq_groupMembers where id=?",
                      (member_id,))
            self.conn.commit()

    def add_group(self, name):
        c = self.cursor
        c.execute("insert into qq_groups (name) "+
                  "values (?)",
                  (name,))
        self.conn.commit()
        c.execute('select id from qq_groups where name=?', (name,))
        group_id = None
        for row in c:
            group_id = row[0]
        return group_id

    def get_group_senders(self, group_id):
        c = self.cursor
        c.execute('select m.number from qq_groupMembers m '+
                  'join qq_sendmap s on m.id=s.memberId '+
                  'where m.groupId=?', (group_id,))
        senders = []
        for row in c:
            senders.append(row[0])
        return senders

    def get_group_admins(self, group_id):
        c = self.cursor
        c.execute('select m.number from qq_groupMembers m '+
                  'join qq_adminmap a on m.id=a.memberId '+
                  'where m.groupId=?', (group_id,))
        admins = []
        for row in c:
            admins.append(row[0])
        return admins

    def get_admin(self, src, dest, msg):
        ''' return pair (cmd, groupId)
        '''
        if not msg.startswith(config.admin_prefix):
            # not an admin command
            return None
        msg = msg[len(config.admin_prefix):]

        c = self.cursor
        c.execute('select a.keyword,m.groupId from qq_groupMembers m '+
                  'join qq_adminmap a on m.id = a.memberId '+
                  'where m.number=? and a.dest=? order by length(keyword) desc',
                  (src,dest))
        for row in c:
            keyword = row[0]
            if len(keyword) > 0: keyword += ' '
            if msg.lower().startswith(keyword.lower()):
                msg_out = msg[len(keyword):]
                return keyword,msg_out,row[1]
        return None

    def get_sendout(self, src, dest, msg):
        ''' return pair (msg, groupId)
        '''
        c = self.cursor
        c.execute('select a.keyword,m.groupId from qq_groupMembers m '+
                  'join qq_sendmap a on m.id = a.memberId '+
                  'where m.number=? and a.dest=? order by length(keyword) desc',
                  (src,dest))
        for row in c:
            keyword = row[0]
            if len(keyword) > 0: keyword += ' '
            if msg.lower().startswith(keyword.lower()):
                msg_out = msg[len(keyword):]
                return msg_out,row[1]
        return None

    def get_group_members(self, group_id):
        c = self.cursor
        c.execute('select number,alias,s.id,a.id from qq_groupMembers m '+
                'left join qq_sendmap s on m.id=s.memberId '+
                'left join qq_adminmap a on m.id=a.memberId '+
                'where m.groupId=?',
                (group_id,))
        members = []
        for row in c:
            sender = row[2] != None
            admin = row[3] != None
            members.append({'number':row[0],'alias':row[1],'sender':sender,'admin':admin})
        return members

    def get_groups(self):
        c = self.cursor
        c.execute('select id,name from qq_groups order by name asc')
        ret = []
        for row in c:
            ret.append(row)
        return ret

    def get_group_id(self,name):
        c = self.cursor
        c.execute('select id,name from qq_groups where name=?', (name,))
        x = c.fetchone()
        if not x:
            return None
        return x[0]

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

    def _calculate_udh_part(self, udh):
        if not udh:
            return None
        length = int(udh[:2], 16)
        i = 1
        while i <= length:
            # parse one IEI
            iei_id = int(udh[i*2:i*2+2], 16)
            i += 1
            iei_len = int(udh[i*2:i*2+2], 16)
            if not iei_id == 0:
                # not concatenation iei
                i += iei_len
                continue
            i += 1
            ref = int(udh[i*2:i*2+2], 16)
            i += 1
            num_parts = int(udh[i*2:i*2+2], 16)
            i += 1
            part = int(udh[i*2:i*2+2], 16)
            return part,num_parts,ref

    def get_unprocessed(self):
        c = self.cursor
        c.execute("select ID,SenderNumber,RecipientID,TextDecoded,UDH "+
                  "from inbox where Processed='false'")
        parts = {}
        ret = []
        for row in c:
            i,src,phone,text,udh = row
            x = self._calculate_udh_part(udh)
            if x:
                part,num_parts,ref = x
                key = src+'-'+str(ref)
                if not key in parts:
                    parts[key] = src,phone,[],[]
                parts[key][2].append((part,text))
                parts[key][3].append(i)

                if len(parts[key][2]) == num_parts:
                    # found all parts
                    tot_text = "".join(map(lambda x: x[1], sorted(parts[key][2], key = lambda x: x[0])))
                    ret.append({'ids':parts[key][3], 'src':src, 'phone':phone, 'text':tot_text})
                    del parts[key]
            else:
                # single part
                ret.append({'ids':[i], 'src':src, 'phone':phone, 'text':text})
        return ret

    def set_processed(self, msgId, status='true'):
        c = self.cursor
        c.execute("update inbox set Processed=? where ID=?", (status,msgId))
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
        c.execute('delete from qq_sendmap')
        c.execute('delete from qq_adminmap')
        self.conn.commit()

    def cleanup(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.conn:
            self.conn.close()
            self.conn = None

class Doer:
    def __init__(self):
        self.smsd = gammu.smsd.SMSD(config.smsdrc)
        self.log = open(config.log, "a")
        self.data = Data()

    def cleanup(self):
        if self.log:
            self.log.close()
            self.log = None
        self.data.cleanup()

    def _log(self, text):
        t = strftime("%Y-%m-%d %H:%M:%S", localtime())
        self.log.write("[%s] [doer] %s\n"%(t,text.encode('utf-8')));
        self.log.flush()

    def send(self, dest, msg):
        # this length calculation will fail will not work for some special
        # gsm7 chars like [
        if len(msg) <= 160: 
            message = {'Text': msg, 'SMSC': {'Location': 1}, 'Number': dest}
            self._log("sending single part message "+str(message))
            self.smsd.InjectSMS([message])
        else:
            # multipart
            self._log("sending multipart message");
            smsinfo = {
                    'Class': 1,
                    'Unicode': False,
                    'Entries':  [{
                            'ID': 'ConcatenatedTextLong',
                            'Buffer': msg
                        }]}
            # Encode messages
            encoded = gammu.EncodeSMS(smsinfo)
            # Send messages
            for message in encoded:
                # Fill in numbers
                message['SMSC'] = {'Location': 1}
                message['Number'] = dest
                # Actually send the message
                self._log("sending part of message: "+str(message));
                self.smsd.InjectSMS([message])

    def run(self):
        self._log("starting doer")
        messages = self.data.get_unprocessed()
        for m in messages:
            ids,src,dest,msg = m['ids'],m['src'],m['phone'],m['text']
            self._log("found message: %s %s->%s '%s'"%(str(ids),src,dest,msg))

            admin_cmd = self.data.get_admin(src,dest,msg)
            sender_cmd = self.data.get_sendout(src,dest,msg)
            status = 'unknown'
            lmsg = msg.lower().strip()
            if lmsg == 'stop' or lmsg == 'stopp':
                for i in self.data.get_member_ids(src):
                    self.data.remove_number(member_id=i)
                status = 'stop'

            if status == 'unknown' and admin_cmd:
                keyword,cmd,group = admin_cmd
                cmd = cmd.lower()
                self._log("doing command '%s' to group %d"%(cmd,group))
                status = 'admin'
                if cmd.startswith('add sender '):
                    number = normalize_number(cmd[len('add sender '):])
                    if number:
                        mid = self.data.add_number(number, 'noname', group)
                        self.data.set_sender(dest, member_id=mid, keyword=keyword)
                    else:
                        self._log("warning: couldn't find number in add command")
                elif cmd.startswith('add admin '):
                    number = normalize_number(cmd[len('add admin '):])
                    if number:
                        mid = self.data.add_number(number, 'noname', group)
                        self.data.set_sender(dest, member_id=mid, keyword=keyword)
                        self.data.set_admin(dest, member_id=mid, keyword=keyword)
                    else:
                        self._log("error: couldn't find number in add command")
                elif cmd.startswith('add '):
                    number = normalize_number(cmd[len('add '):])
                    if number:
                        self.data.add_number(number, 'noname', group)
                    else:
                        self._log("error: couldn't find number in add command")
                else:
                    self._log("error: unknown admin command!")

            if status == 'unknown' and sender_cmd:
                msg,group = sender_cmd
                self._log("doing sendout to group %d"%group)
                members = self.data.get_group_members(group)
                for member in members:
                    self.send(member['number'],msg)
                status = 'send'

            for i in ids:
                self.data.set_processed(i,status)
        self.cleanup()

