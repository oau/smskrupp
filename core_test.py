import core
from config import config

class TestData:
    def setUp(self):
        config.db = config.test_db
        config.smsdrc = config.test_smsdrc
        self.data = core.Data()
        self.data.setup_db()
        self.data.purge_all_data()

    def test_add_group(self):
        gid = self.data.add_group("group1", "keyword", "phone1")
        assert isinstance(gid, int)
        gs = self.data.get_groups(phone="phone1")
        assert 1 == len(gs)
        assert 'group1' == gs[0]['name']
        assert 'keyword' == gs[0]['keyword']
        assert 'phone1' == gs[0]['phone']
        assert gid == gs[0]['id']

    def test_get_groups(self):
        number1 = "345"
        number2 = "346"
        phone = "phone1"
        gid1 = self.data.add_group("group1", "keyword1", phone)
        gid2 = self.data.add_group("group2", "keyword2", phone)
        self.data.add_number(number1, "alias", gid1)
        self.data.add_number(number2, "alias", gid2)
        gs = self.data.get_groups(phone=phone)
        assert 2 == len(gs)

        gs = self.data.get_groups(phone=phone,sender=number1)
        assert 1 == len(gs)
        assert 'group1' == gs[0]['name']

        gs = self.data.get_groups(sender=number2)
        assert 1 == len(gs)
        assert 'group2' == gs[0]['name']

    def test_add_number(self):
        number = "123"
        gid = self.data.add_group("group1", "keyword", "123")
        mid = self.data.add_number(number, "alias", gid)
        members = self.data.get_group_members(gid)
        assert mid
        assert len(members) == 1
        assert members[0]['id'] == mid
        assert members[0]['number'] == number
        assert members[0]['alias'] == 'alias'

    def test_add_number_no_alias(self):
        number1 = "123"
        number2 = "124"
        gid = self.data.add_group("group1", "keyword", "123")
        mid = self.data.add_number(number1, None, gid)
        mid2 = self.data.add_number(number2, None, gid)
        members = self.data.get_group_members(gid)
        assert mid
        assert mid2
        assert len(members) == 2
        assert members[0]['id'] == mid
        assert members[0]['number'] == number1
        assert members[0]['alias'] == 'noname1'
        assert members[1]['id'] == mid2
        assert members[1]['number'] == number2
        assert members[1]['alias'] == 'noname2'

    def test_remove_number(self):
        number1 = "123"
        number2 = "1235"
        gid = self.data.add_group("group1", "keyword", "123")
        self.data.add_number(number1, "alias", gid)
        self.data.remove_number(number=number1, group_id=gid)
        numbers = self.data.get_group_members(gid)
        assert len(numbers) == 0

        mid = self.data.add_number(number2, "alias", gid)
        self.data.remove_number(member_id=mid)
        numbers = self.data.get_group_members(gid)
        assert len(numbers) == 0

    def test_add_sender(self):
        number = "1234"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_member_info(mid, sender=True, admin=True)
        senders = self.data.get_group_senders(gid)
        assert len(senders) == 1
        assert number == senders[0]['number']
        assert mid == senders[0]['id']
        assert 'alias' == senders[0]['alias']

    def test_add_admin(self):
        number = "1234"
        phone = "phone1337"
        gid = self.data.add_group("group1", "", phone)
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_member_info(member_id=mid, admin=True)
        admins = self.data.get_group_admins(gid)
        assert len(admins) == 1
        assert number == admins[0]['number']
        assert mid == admins[0]['id']
        assert 'alias' == admins[0]['alias']

    def test_get_unprocessed(self):
        number1 = "+46730000009"
        self.data.fake_incoming(number1, "phone1", "hello")
        u = self.data.get_unprocessed()
        assert len(u) == 1
        assert number1 == u[0]['src']
        assert "phone1" == u[0]['phone']
        assert "hello" == u[0]['text']

class TestDoer:
    def setUp(self):
        config.db = config.test_db
        config.smsdrc = config.test_smsdrc
        self.sender = FakeSender() #core.Sender()
        self.doer = core.Doer(self.sender)
        self.data = core.Data()
        self.data.setup_db()
        self.data.purge_all_data()

    def test_run(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", "123")
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_member_info(mid, sender=True)
        self.data.fake_incoming(number, phone, "hello")
        self.doer.run()

    def test_run_stop_command(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        self.data.add_number(number, "alias", gid)
        self.data.fake_incoming(number, phone, "stop")
        self.doer.run()
        assert 0 == len(self.data.get_group_members(gid))

    def test_run_stop_command_prefix(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        self.data.add_number(number, "alias", gid)
        self.data.fake_incoming(number, phone, "/keyword stop")
        self.doer.run()
        assert 0 == len(self.data.get_group_members(gid))

    def test_run_admin_command_add_unauthorized(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        self.data.add_number(number, "alias", gid)
        self.data.fake_incoming(number, phone, "/add 073123")
        self.doer.run()
        assert not "+4673123" in [x['number'] for x in self.data.get_group_members(gid)]
        assert not "+4673123" in [x['number'] for x in self.data.get_group_senders(gid)]
        assert not "+4673123" in [x['number'] for x in self.data.get_group_admins(gid)]
        assert len(self.sender.sendouts) == 0 # no welcome message

    def test_run_admin_command_add(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_member_info(mid, sender=True, admin=True)
        self.data.fake_incoming(number, phone, "/add 073123")
        self.doer.run()
        assert "+4673123" in [x['number'] for x in self.data.get_group_members(gid)]
        assert not "+4673123" in [x['number'] for x in self.data.get_group_senders(gid)]
        assert not "+4673123" in [x['number'] for x in self.data.get_group_admins(gid)]
        assert len(self.sender.sendouts) == 1 # welcome message
        assert self.sender.sendouts[0][0] == "+4673123"

    def test_run_admin_command_add_sender(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_member_info(mid, sender=True, admin=True)
        self.data.fake_incoming(number, phone, "/Add Sender 073123")
        self.doer.run()
        assert "+4673123" in [x['number'] for x in self.data.get_group_members(gid)]
        assert "+4673123" in [x['number'] for x in self.data.get_group_senders(gid)]
        assert not "+4673123" in [x['number'] for x in self.data.get_group_admins(gid)]
        assert len(self.sender.sendouts) == 1 # welcome message
        assert self.sender.sendouts[0][0] == "+4673123"

    def test_run_admin_command_add_admin(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_member_info(mid, sender=True, admin=True)
        self.data.fake_incoming(number, phone, "/add admin 073123")
        self.doer.run()
        assert "+4673123" in [x['number'] for x in self.data.get_group_members(gid)]
        assert "+4673123" in [x['number'] for x in self.data.get_group_senders(gid)]
        assert "+4673123" in [x['number'] for x in self.data.get_group_admins(gid)]
        assert len(self.sender.sendouts) == 1 # welcome message
        assert self.sender.sendouts[0][0] == "+4673123"

    def test_run_admin_command_add_keyword(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_member_info(mid, sender=True, admin=True)
        self.data.fake_incoming(number, phone, "/keyword add 073123")
        self.doer.run()
        assert "+4673123" in [x['number'] for x in self.data.get_group_members(gid)]
        assert not "+4673123" in [x['number'] for x in self.data.get_group_senders(gid)]
        assert not "+4673123" in [x['number'] for x in self.data.get_group_admins(gid)]
        assert len(self.sender.sendouts) == 1 # welcome message
        assert self.sender.sendouts[0][0] == "+4673123"

    def test_run_admin_command_add_sender_keyword(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_member_info(mid, sender=True, admin=True)
        self.data.fake_incoming(number, phone, "/KEYWORD Add Sender 073123")
        self.doer.run()
        assert "+4673123" in [x['number'] for x in self.data.get_group_members(gid)]
        assert "+4673123" in [x['number'] for x in self.data.get_group_senders(gid)]
        assert not "+4673123" in [x['number'] for x in self.data.get_group_admins(gid)]
        assert len(self.sender.sendouts) == 1 # welcome message
        assert self.sender.sendouts[0][0] == "+4673123"

    def test_run_admin_command_add_admin_keyword(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_member_info(mid, sender=True, admin=True)
        self.data.fake_incoming(number, phone, "/KEyWord add admin 073123")
        self.doer.run()
        assert "+4673123" in [x['number'] for x in self.data.get_group_members(gid)]
        assert "+4673123" in [x['number'] for x in self.data.get_group_senders(gid)]
        assert "+4673123" in [x['number'] for x in self.data.get_group_admins(gid)]
        assert len(self.sender.sendouts) == 1 # welcome message
        assert self.sender.sendouts[0][0] == "+4673123"

    def test_run_sendout_unauthorized(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        self.data.add_number(number, "alias", gid)

        s = FakeSender()
        doer = core.Doer(s)
        self.data.fake_incoming(number, phone, "test")
        doer.run()
        assert 0 == len(s.sendouts)

    def test_run_sendout_keyword_unauthorized(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        self.data.add_number(number, "alias", gid)

        s = FakeSender()
        doer = core.Doer(s)
        self.data.fake_incoming(number, phone, "#keyword test")
        doer.run()
        assert 0 == len(s.sendouts)

    def test_run_sendout(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_member_info(mid, sender=True)

        s = FakeSender()
        doer = core.Doer(s)
        self.data.fake_incoming(number, phone, "test")
        doer.run()
        assert 1 == len(s.sendouts)
        assert (number, "#keyword test") == s.sendouts[0]

    def test_run_sendout_prefix(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1", "keyword", phone)
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_member_info(mid, sender=True)

        s = FakeSender()
        doer = core.Doer(s)
        self.data.fake_incoming(number, phone, "#keyword test")
        doer.run()
        assert 1 == len(s.sendouts)
        assert (number, "#keyword test") == s.sendouts[0]

class FakeSender:
    def __init__(self):
        self.sendouts = []

    def send(self, dest, msg):
        self.sendouts.append((dest,msg))
