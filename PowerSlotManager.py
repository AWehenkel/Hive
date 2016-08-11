import MySQLdb

class PowerSlotManager:
    def __init__(self):
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        request = "SELECT id_station,begin_time FROM power_slot WHERE id_vehicle = -1"
        cursor.execute(request)
        datas = cursor.fetchall()
        self.power_slot = {}
        for data in datas:
            key = "%d-%d" % (data[0], data[1])
            if self.power_slot.has_key(key):
                self.power_slot[key] += 1
            else:
                self.power_slot[key] = 1

    def isFree(self, id_station, begin_time, nb_slot=1):
        for slot in range(begin_time, begin_time + nb_slot):
            key = "%d-%d" % (id_station, slot)
            if(not(self.power_slot.has_key(key) and self.power_slot[key] > 0)):
                return 0
        return 1

    def bookSlot(self, id_station, begin_time, nb_slot, id_car):
        db = MySQLdb.connect("localhost", "root", "videogame2809", "hive")
        cursor = db.cursor()
        for slot in range(0, nb_slot):
            key = "%d-%d" % (id_station, begin_time + slot)
            if(self.isFree(id_station, begin_time + slot)):
                self.power_slot[key] -= 1
                print self.power_slot[key]
                request = "SELECT min(id) FROM power_slot WHERE id_station=%d AND begin_time=%d" % (
                    id_station, begin_time + slot)
                print request
                cursor.execute(request)
                id_slot = cursor.fetchone()
                request = "UPDATE power_slot SET id_vehicle=%d WHERE id=%d" % (id_car, id_slot[0])
                print request
                cursor.execute(request)
        db.commit()

    def resetBooking(self):
        print "todo"

t = PowerSlotManager()
print t.isFree(1, 8, 12)