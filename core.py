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

    def get_unprocessed(self):
        c = self.cursor
        c.execute("select ID,SenderNumber,RecipientID,TextDecoded "+
                  "from inbox where Processed='false'")
        ret = []
        for row in c:
            ret.append(row)
        return ret

    def set_processed(self, msgId):
        c = self.cursor
        c.execute("update inbox set Processed='true' where ID=?", (msgId,))
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
        self.cursor.close()
        self.conn.close()

class Worker:
    def __init__(self):
        self.smsd = gammu.smsd.SMSD(config.smsdrc)
        self.log = open(config.log, "a")
        self.data = Data()

    def _cleanup(self):
        self.log.close()
        self.data.cleanup()

    def _log(self, text):
        t = strftime("%Y-%m-%d %H:%M:%S", localtime())
        self.log.write("[%s] [worker] %s\n"%(t,text.encode('utf-8')));
        self.log.flush()

    def send(self, dest, msg):
        msg = msg.decode('UTF-8')
        message = {'Text': msg, 'SMSC': {'Location': 1}, 'Number': dest}
        self._log("sending "+str(message))
        self.smsd.InjectSMS([message])

    def run(self):
        self._log("starting worker")
        messages = self.data.get_unprocessed()
        for m in messages:
            i,src,dest,msg = m
            self._log("found message: [%d] %s->%s '%s'"%(i,src,dest,msg))
            a = self.data.get_admin(src,dest,msg)
            if a:
                keyword,cmd,group = a
                self._log("doing command '%s' to group %d"%(cmd,group))
                if cmd.startswith('add sender '):
                    number = normalize_number(cmd[len('add sender '):])
                    if number:
                        mid = self.data.add_number(number, 'noname', group)
                        self.data.set_sender(dest, member_id=mid, keyword=keyword)
                    else:
                        self._log("error: couldn't find number in add command")
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

            s = self.data.get_sendout(src,dest,msg)
            if s:
                msg,group = s
                self._log("doing sendout to group %d"%group)
                members = self.data.get_group_members(group)
                for member in members:
                    self.send(member['number'],msg)

            self.data.set_processed(i)
        self._cleanup()

