import time

import adafruit_dht


class DHT22Sensor:
    def __init__(self, pin):
        self.pin = pin
        self.dht_sensor = self.init_sensor()

    def init_sensor(self):
        return adafruit_dht.DHT22(self.pin)

    def reinit_sensor(self):
        self.dht_sensor.exit()
        self.dht_sensor = self.init_sensor()
        time.sleep(1)

    def _get_data(self, param: str) -> float:
        try:
            return getattr(self.dht_sensor, param)
        except RuntimeError as error:
            # Errors happen fairly often, DHT is hard to read, just keep going
            print(error.args[0])
        except Exception as error:
            print(f"Unknown error occurred - {error}.\nSensor will be reinitialized")
            self.reinit_sensor()

    def get_temperate(self) -> float:
        param = "temperature"
        return self._get_data(param)

    def get_humidity(self) -> float:
        param = "humidity"
        return self._get_data(param)
