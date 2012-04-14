import core
from config import config

def nomalize_number(number):
    if number[:2] == '07':
        return '+46'+number[1:]
    return number

class TestData:
    def setUp(self):
        config.db = config.test_db
        self.data = core.Data()
        self.data.setup_db()
        self.data.purge_all_data()

    def test_add_group(self):
        gid = self.data.add_group("group1")
        assert isinstance(gid, int)

    def test_add_number(self):
        number = "123"
        gid = self.data.add_group("group1")
        mid = self.data.add_number(number, "alias", gid)
        members = self.data.get_group_members(gid)
        assert mid
        assert len(members) == 1
        assert members[0]['number'] == number
        assert members[0]['alias'] == 'alias'

    def test_remove_number(self):
        number1 = "123"
        number2 = "1235"
        gid = self.data.add_group("group1")
        self.data.add_number(number1, "alias", gid)
        self.data.remove_number(number=number1, group_id=gid)
        numbers = self.data.get_group_members(gid)
        assert len(numbers) == 0

        mid = self.data.add_number(number2, "alias", gid)
        self.data.remove_number(member_id=mid)
        numbers = self.data.get_group_members(gid)
        assert len(numbers) == 0

    def test_add_sender(self):
        number1 = "1234"
        dest = "7777"
        gid = self.data.add_group("group1")
        mid = self.data.add_number(number1, "alias", gid)
        self.data.set_sender(dest, member_id=mid)
        self.data.set_admin(dest, member_id=mid)
        msg,group = self.data.get_sendout(number1, dest, "hello")
        assert msg == "hello"
        assert group == gid

    def test_add_admin(self):
        number1 = "1234"
        dest = "7777"
        gid = self.data.add_group("group1")
        mid = self.data.add_number(number1, "alias", gid)
        self.data.set_admin(dest, member_id=mid)
        kw,cmd,group = self.data.get_admin(number1, dest, "hello")
        assert kw == ""
        assert cmd == "hello"
        assert group == gid

    def test_get_unprocessed(self):
        number1 = "+46730000009"
        self.data.fake_incoming(number1, "phone1", "hello")
        u = self.data.get_unprocessed()
        assert len(u) == 1
        #i,src,phone,txt = u[0]
        assert number1 == u[0]['src']
        assert "phone1" == u[0]['phone']
        assert "hello" == u[0]['text']

class TestWorker:
    def setUp(self):
        self.worker = core.Worker()
        self.data = core.Data()
        self.data.setup_db()
        self.data.purge_all_data()

    def test_run(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1")
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_sender(phone, member_id = mid)
        self.data.fake_incoming(number, phone, "hello")
        self.worker.run()

    def test_run_admin_command_add(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1")
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_admin(phone, member_id = mid)
        self.data.fake_incoming(number, phone, "add 073123")
        self.worker.run()
        assert "+4673123" in map(lambda x: x['number'], self.data.get_group_members(gid))
        assert not "+4673123" in self.data.get_group_senders(gid)
        assert not "+4673123" in self.data.get_group_admins(gid)

    def test_run_admin_command_add_sender(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1")
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_admin(phone, member_id = mid)
        self.data.fake_incoming(number, phone, "add sender 073123")
        self.worker.run()
        assert "+4673123" in map(lambda x: x['number'],
                                 self.data.get_group_members(gid))
        assert "+4673123" in self.data.get_group_senders(gid)
        assert not "+4673123" in self.data.get_group_admins(gid)

    def test_run_admin_command_add_admin(self):
        number = "+46736000001"
        phone = "phone1"
        gid = self.data.add_group("group1")
        mid = self.data.add_number(number, "alias", gid)
        self.data.set_admin(phone, member_id = mid)
        self.data.fake_incoming(number, phone, "add admin 073123")
        self.worker.run()
        assert "+4673123" in map(lambda x: x['number'],
                                 self.data.get_group_members(gid))
        assert "+4673123" in self.data.get_group_senders(gid)
        assert "+4673123" in self.data.get_group_admins(gid)
