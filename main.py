import signal
import sys
import time
from datetime import datetime

import board

import config
from db.sqlite_connector import SensorsDataDbHandler
from sensors.dht22 import DHT22Sensor
from sensors.mq2 import MQ2Sensor


def main():

    def _handle_stop_signal(*args):
        print("Closing database connections before exit")
        db.db_teardown()
        print("Exiting with sys code 0")
        sys.exit(0)

    db = SensorsDataDbHandler(config.db_path)

    signal.signal(signal.SIGINT, _handle_stop_signal)
    signal.signal(signal.SIGTERM, _handle_stop_signal)

    dht_22 = DHT22Sensor(board.D4)
    mq2 = MQ2Sensor()
    db.init_dht_table()
    db.init_mq2_table()

    while True:
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temp, hum = dht_22.get_temperate(), dht_22.get_humidity()
        mq_data = mq2.mq_percentage()

        db.insert_dht_data(date, temp, hum)
        db.insert_mq2_data(date, mq_data)

        time.sleep(60)


if __name__ == "__main__":
    main()
