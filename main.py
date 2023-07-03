import time
from datetime import datetime

import board

from db.sqlite_connector import SensorsDataDbHandler
from sensors.dht22 import DHT22Sensor
from sensors.mq2 import MQ2Sensor


def main():
    dht_22 = DHT22Sensor(board.D4)
    mq2 = MQ2Sensor()
    db = SensorsDataDbHandler('sensors_data.db')
    db.init_dht_table()
    db.init_mq2_table()

    while True:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temp, hum = dht_22.get_temperate(), dht_22.get_humidity()
        mq_data = mq2.mq_percentage()

        db.insert_dht_data(date, temp, hum)
        db.insert_mq2_data(date, mq_data)

        time.sleep(30)


if __name__ == "__main__":
    main()
