import logging
import json
import time
import os
import re
from datetime import datetime
import requests
import mysql.connector
from signalrcore.hub_connection_builder import HubConnectionBuilder

# Connection parameters
db_config = {
    "host": "127.0.0.1",
    "user": "root",
    "password": "password",
    "database": "githubmetrics",
}


def format_timestamp(timestamp_str):
    """Function to format the date and adapt it to the database format datetime"""
    match = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", timestamp_str)
    if match:
        formatted_timestamp = match.group(0)
        return formatted_timestamp

    raise ValueError("Formato de timestamp no válido")


class Main:
    """
    Class that manages all requests and answer from the server and
    with the required functions to control the temperature of the room.
    """

    def __init__(self):
        """Setup environment variables and default values."""
        self._hub_connection = None
        # pylint: disable=C0103
        # (it unables snack_case restriction for the following variable
        #  in the pre-commit hook)
        self.HOST = os.environ.get(
            "OXYGEN_HOST"
        )  # Setup your host here: https://hvac-simulator-a23-y2kpq.ondigitalocean.app
        self.TOKEN = os.environ.get("OXYGEN_TOKEN")  # Setup your token here: QWNTDxtJzo

        self.TICKETS = 2  # Setup your tickets here
        self.T_MAX = 16  # Setup your max temperature here
        self.T_MIN = 10  # Setup your min temperature here
        self.DATABASE = mysql.connector.connect(**db_config)  # Setup your database here

    def __del__(self):
        if self._hub_connection is not None:
            self._hub_connection.stop()

    def setup(self):
        """Setup Oxygen CS."""
        self.set_sensorhub()

    def start(self):
        """Start Oxygen CS."""
        self.setup()
        self._hub_connection.start()

        print("Press CTRL+C to exit.", flush=True)
        while True:
            time.sleep(2)

    def set_sensorhub(self):
        """Configure hub connection and subscribe to sensor data events."""
        self._hub_connection = (
            HubConnectionBuilder()
            .with_url(f"{self.HOST}/SensorHub?token={self.TOKEN}")
            .configure_logging(logging.INFO)
            .with_automatic_reconnect(
                {
                    "type": "raw",
                    "keep_alive_interval": 10,
                    "reconnect_interval": 5,
                    "max_attempts": 999,
                }
            )
            .build()
        )

        self._hub_connection.on("ReceiveSensorData", self.on_sensor_data_received)
        self._hub_connection.on_open(
            lambda: print("||| Connection opened.", flush=True)
        )
        self._hub_connection.on_close(
            lambda: print("||| Connection closed.", flush=True)
        )
        self._hub_connection.on_error(
            lambda data: print(
                f"||| An exception was thrown closed: {data.error}", flush=True
            )
        )

    def on_sensor_data_received(self, data):
        """Callback method to handle sensor data on reception."""
        # pylint: disable=broad-exception-caught
        try:
            print(data[0]["date"] + " --> " + data[0]["data"], flush=True)
            date = data[0]["date"]
            temperature = float(data[0]["data"])
            self.take_action(temperature, date)
            self.send_event_to_database(date, temperature)
        except Exception as err:
            print(err, flush=True)

    def take_action(self, temperature, timestamp):
        """Take action to HVAC depending on current temperature."""
        if float(temperature) >= float(self.T_MAX):
            self.send_action_to_hvac("TurnOnAc")
            self.send_event_to_database(timestamp, "TurnOnAc")
        elif float(temperature) <= float(self.T_MIN):
            self.send_action_to_hvac("TurnOnHeater")
            self.send_event_to_database(timestamp, "TurnOnHeater")

    def send_action_to_hvac(self, action):
        """Send action query to the HVAC service."""
        r = requests.get(
            f"{self.HOST}/api/hvac/{self.TOKEN}/{action}/{self.TICKETS}", timeout=10
        )
        details = json.loads(r.text)
        print(details, flush=True)

    # pylint: disable=unused-argument, unused-variable
    def send_event_to_database(self, timestamp, event):
        """Save sensor data into database."""
        datetime_mariadb = format_timestamp(timestamp)
        datetime_mariadb = datetime.fromisoformat(datetime_mariadb)
        datetime_mariadb = datetime_mariadb.strftime("%Y-%m-%d %H:%M:%S.%f")
        try:
            cursor = self.DATABASE.cursor()
            if event in ("TurnOnAc", "TurnOnHeater"):
                query = (
                    f"INSERT INTO eventoxygencs VALUES('{event}','{datetime_mariadb}')"
                )
                cursor.execute(query)
                self.DATABASE.commit()

            else:
                query = (
                    f"INSERT INTO hvactemperature VALUES({event},'{datetime_mariadb}')"
                )
                cursor.execute(query)
                self.DATABASE.commit()

            cursor.close()

        except mysql.connector.Error as error:
            print(f"ERROR WITH DB: {error}")


if __name__ == "__main__":
    # Test
    main = Main()
    main.start()
