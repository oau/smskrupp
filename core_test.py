import core
from config import config

def nomalize_number(number):
    if number[:2] == '07':
        return '+46'+number[1:]
    return number

class TestData:
    def setUp(self):
        config.db = "tmp.db"
        self.data = core.Data()
        self.data.setup_db()
        self.data.purge_all_data()

    def test_add_group(self):
        gid = self.data.add_group("group1")
        assert isinstance(gid, int)

    def test_add_number(self):
        number = "123"
        gid = self.data.add_group("group1")
        self.data.add_number(number, "alias", gid)
        members = self.data.get_group_members(gid)
        assert len(members) == 1
        assert members[0]['number'] == number
        assert members[0]['alias'] == 'alias'

    def test_remove_number(self):
        number = "123"
        gid = self.data.add_group("group1")
        self.data.add_number(number, "alias", gid)
        self.data.remove_number(number, gid)
        numbers = self.data.get_group_members(gid)
        assert len(numbers) == 0

    def test_add_sender(self):
        number1 = "1234"
        number2 = "7777"
        gid = self.data.add_group("group1")
        self.data.add_number(number1, "alias", gid)
        self.data.add_sender(number1, number2, gid)
        msg,group = self.data.get_sendout(number1, number2, "hello")
        assert msg == "hello"
        assert group == gid

    def test_get_unprocessed(self):
        number1 = "+46730000009"
        self.data.fake_incoming(number1, "phone1", "hello")
        u = self.data.get_unprocessed()
        assert len(u) == 1
        i,src,phone,txt = u[0]
        assert src == number1
        assert phone == "phone1"
        assert txt == "hello"

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
        self.data.add_number(number, "alias", gid)
        self.data.add_sender(number, phone, gid)
        self.data.fake_incoming(number, phone, "hello")
        self.worker.run()
