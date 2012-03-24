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
                  "src varchar(22) not null, dest varchar(22) not null, "+
                  "keyword varchar(32) not null, groupId int not null)")
        self.conn.commit()

    def add_number(self, number, alias, group_id):
        c = self.cursor
        c.execute("insert into qq_groupMembers "+
                  "(number, groupId, alias) "+
                  "values (?,?,?)",
                  (number, group_id, alias))
        self.conn.commit()

    def add_sender(self, number, dest, group_id, keyword=""):
        c = self.cursor
        c.execute("insert into qq_sendmap (src,dest,keyword,groupId) "+
                  "values (?,?,?,?)",
                  (number, dest, keyword, group_id))
        self.conn.commit()

    def remove_number(self, number, group_id):
        c = self.cursor
        c.execute("delete from qq_groupMembers where number=? and groupId=?",
                  (number, group_id))
        c.execute("delete from qq_sendmap where src=? and groupId=?",
                  (number, group_id))
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
        c.execute('select src from qq_sendmap '+
                  'where groupId=?', (group_id,))
        senders = []
        for row in c:
            senders.append(row[0])
        return senders

    def get_sendout(self, src, dest, msg):
        ''' return pair (msg, groupId)
        '''
        c = self.cursor
        c.execute('select keyword,groupId from qq_sendmap '+
                  'where src=? and dest=? order by length(keyword) desc', (src,dest))
        for row in c:
            keyword = row[0]
            if len(keyword) > 0: keyword += ' '
            if msg.lower().startswith(keyword.lower()):
                msg_out = msg[len(keyword):]
                return msg_out,row[1]
        return None

    def get_group_members(self, group_id):
        c = self.cursor
        c.execute('select number,alias from qq_groupMembers where groupId=?', (group_id,))
        members = []
        for row in c:
            members.append({'number':row[0],'alias':row[1]})
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
        self.log.write("[%s] [worker] %s\n"%(t,text));
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
            s = self.data.get_sendout(src,dest,msg)
            if s:
                msg,group = s
                self._log("doing sendout to group %d"%group)
                members = self.data.get_group_members(group)
                for member in members:
                    self.send(member['number'],msg)

            self.data.set_processed(i)
        self._cleanup()

