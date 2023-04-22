"""
WeeWX Prometheus Exporter

This module provides a WeeWX service that exports weather station metrics
to a Prometheus-compatible format. The PrometheusService class listens for
new loop packets from WeeWX, converts the metrics to Prometheus-compatible
metric names, and updates or creates corresponding gauges. The module also
starts an HTTP server to serve the metrics in a format that can be easily
scraped by a Prometheus server.

Mappings between WeeWX metric names and Prometheus metric names are defined
in the WEEWX_TO_PROMETHEUS_MAPPING constant. If new WeeWX metrics are added,
please update this constant with appropriate Prometheus metric names and
descriptions.

Example usage:
1. Add this module to your WeeWX installation.
2. Update your WeeWX configuration to include the PrometheusService as a service.
3. Start WeeWX and access the metrics at http://<your_weewx_host>:8000/.
"""

# Standard Python Libraries
import logging

# Third-Party Libraries
from prometheus_client import Gauge, start_http_server
from prometheus_client.core import CollectorRegistry
import weewx

log = logging.getLogger(__name__)

WEEWX_TO_PROMETHEUS_MAPPING = {
    # fmt: off
    'ET': ('weewx_evapotranspiration', 'Evapotranspiration in inches or millimeters'),
    'UV': ('weewx_uv_index', 'Ultraviolet index'),
    'a3': ('weewx_ozone', 'Ozone (ppb)'),
    'altimeter': ('weewx_altimeter', 'Altimeter pressure in inHg or hPa'),
    'appTemp': ('weewx_apparent_temperature_celsius', 'Apparent temperature (°F/°C)'),
    'appTemp1': ('weewx_apparent_temperature_1', 'Apparent Temperature Sensor 1 (°F/°C)'),
    'barometer': ('weewx_barometer', 'Barometric pressure in inHg or hPa'),
    'batteryStatus2': ('weewx_battery_status_2', 'Battery Status for Sensor 2'),
    'batteryStatus3': ('weewx_battery_status_3', 'Battery Status for Sensor 3'),
    'batteryStatus4': ('weewx_battery_status_4', 'Battery Status for Sensor 4'),
    'batteryStatus5': ('weewx_battery_status_5', 'Battery Status for Sensor 5'),
    'batteryStatus6': ('weewx_battery_status_6', 'Battery Status for Sensor 6'),
    'batteryStatus7': ('weewx_battery_status_7', 'Battery Status for Sensor 7'),
    'batteryStatus8': ('weewx_battery_status_8', 'Battery Status for Sensor 8'),
    'cloudbase': ('weewx_cloudbase_meters', 'Estimated cloud base height in meters'),
    'co': ('weewx_carbon_monoxide', 'Carbon Monoxide (ppm)'),
    'co2': ('weewx_carbon_dioxide', 'Carbon Dioxide (ppm)'),
    'consBatteryVoltage': ('weewx_console_battery_voltage', 'Console battery voltage in volts'),
    'dateTime': ('weewx_datetime_seconds', 'UNIX timestamp of the WeeWX loop packet'),
    'dewpoint': ('weewx_dewpoint', 'Dew point temperature (°F/°C)'),
    'dewpoint1': ('weewx_dewpoint_1', 'Dewpoint Sensor 1 (°F/°C)'),
    'extraHumid1': ('weewx_extra_humidity_1', 'Extra humidity for sensor 1 (%)'),
    'extraHumid2': ('weewx_extra_humidity_2', 'Extra Humidity Sensor 2 (%)'),
    'extraHumid3': ('weewx_extra_humidity_3', 'Extra Humidity Sensor 3 (%)'),
    'extraHumid4': ('weewx_extra_humidity_4', 'Extra Humidity Sensor 4 (%)'),
    'extraHumid5': ('weewx_extra_humidity_5', 'Extra Humidity Sensor 5 (%)'),
    'extraHumid6': ('weewx_extra_humidity_6', 'Extra Humidity Sensor 6 (%)'),
    'extraHumid7': ('weewx_extra_humidity_7', 'Extra Humidity Sensor 7 (%)'),
    'extraHumid8': ('weewx_extra_humidity_8', 'Extra Humidity Sensor 8 (%)'),
    'extraTemp1': ('weewx_extra_temperature_1', 'Extra temperature for sensor 1 (°F/°C)'),
    'extraTemp2': ('weewx_extra_temperature_2', 'Extra Temperature Sensor 2 (°F/°C)'),
    'extraTemp3': ('weewx_extra_temperature_3', 'Extra Temperature Sensor 3 (°F/°C)'),
    'extraTemp4': ('weewx_extra_temperature_4', 'Extra Temperature Sensor 4 (°F/°C)'),
    'extraTemp5': ('weewx_extra_temperature_5', 'Extra Temperature Sensor 5 (°F/°C)'),
    'extraTemp6': ('weewx_extra_temperature_6', 'Extra Temperature Sensor 6 (°F/°C)'),
    'extraTemp7': ('weewx_extra_temperature_7', 'Extra Temperature Sensor 7 (°F/°C)'),
    'extraTemp8': ('weewx_extra_temperature_8', 'Extra Temperature Sensor 8 (°F/°C)'),
    'hail': ('weewx_hail', 'Hail in number of hailstones'),
    'hailRate': ('weewx_hail_rate', 'Hail rate in number of hailstones per hour'),
    'heatindex': ('weewx_heat_index', 'Heat index temperature (°F/°C)'),
    'heatindex1': ('weewx_heat_index_1', 'Heat Index Sensor 1 (°F/°C)'),
    'heatingTemp': ('weewx_heating_temperature', 'Heating temperature (°F/°C)'),
    'heatingVoltage': ('weewx_heating_voltage', 'Heating voltage in volts'),
    'humidex': ('weewx_humidex_celsius', 'Humidex temperature (°F/°C)'),
    'humidex1': ('weewx_humidex_1', 'Humidex Sensor 1 (°F/°C)'),
    'inDewpoint': ('weewx_indoor_dewpoint_celsius', 'Indoor dewpoint temperature (°F/°C)'),
    'inHumidity': ('weewx_indoor_humidity', 'Indoor relative humidity (%)'),
    'inTemp': ('weewx_indoor_temperature', 'Indoor temperature (°F/°C)'),
    'inTempBatteryStatus': ('weewx_indoor_temperature_battery_status', 'Battery status of the indoor temperature sensor'),
    'insolation': ('weewx_insolation', 'Insolation in Langley units (calories per square centimeter)'),
    'interval': ('weewx_interval', 'Archive interval in minutes'),
    'leafTemp1': ('weewx_leaf_temperature_1', 'Leaf temperature for sensor 1 (°F/°C)'),
    'leafTemp2': ('weewx_leaf_temperature_2', 'Leaf temperature for sensor 2 (°F/°C)'),
    'leafWet1': ('weewx_leaf_wetness_1', 'Leaf wetness for sensor 1'),
    'leafWet2': ('weewx_leaf_wetness_2', 'Leaf wetness for sensor 2'),
    'lightning_distance': ('weewx_lightning_distance', 'Lightning Distance (km/miles)'),
    'lightning_disturber_count': ('weewx_lightning_disturber_count', 'Lightning Disturber Count'),
    'lightning_energy': ('weewx_lightning_energy', 'Lightning Energy'),
    'lightning_noise_count': ('weewx_lightning_noise_count', 'Lightning Noise Count'),
    'lightning_strike_count': ('weewx_lightning_strike_count', 'Lightning Strike Count'),
    'luminosity': ('weewx_luminosity', 'Luminosity (lux)'),
    'nh3': ('weewx_ammonia', 'Ammonia (ppm)'),
    'no2': ('weewx_nitrogen_dioxide', 'Nitrogen Dioxide (ppm)'),
    'noise': ('weewx_noise', 'Noise (dB)'),
    'outHumidity': ('weewx_outdoor_humidity', 'Outdoor relative humidity (%)'),
    'outTemp': ('weewx_outdoor_temperature', 'Outdoor temperature (°F/°C)'),
    'outTempBatteryStatus': ('weewx_outdoor_temperature_battery_status', 'Outdoor Temperature Battery Status'),
    'pb': ('weewx_lead', 'Lead (ppb)'),
    'pm10_0': ('weewx_pm10_0', 'Particulate Matter 10.0 (µg/m³)'),
    'pm1_0': ('weewx_pm1_0', 'Particulate Matter 1.0 (µg/m³)'),
    'pm2_5': ('weewx_pm2_5', 'Particulate Matter 2.5 (µg/m³)'),
    'pressure': ('weewx_pressure', 'Station pressure in inHg or hPa'),
    'radiation': ('weewx_solar_radiation', 'Solar radiation in Watts per square meter'),
    'rain': ('weewx_rain', 'Rainfall since the last archive record in inches or millimeters'),
    'rainBatteryStatus': ('weewx_rain_battery_status', 'Battery status of the rain sensor'),
    'rainRate': ('weewx_rain_rate', 'Rain rate in inches per hour or millimeters per hour'),
    'referenceVoltage': ('weewx_reference_voltage', 'Reference voltage in volts'),
    'rxCheckPercent': ('weewx_rx_check_percent', 'Percentage of radio checks received by the console'),
    'signal2': ('weewx_signal_strength_2', 'Signal Strength for Sensor 2'),
    'signal3': ('weewx_signal_strength_3', 'Signal Strength for Sensor 3'),
    'signal4': ('weewx_signal_strength_4', 'Signal Strength for Sensor 4'),
    'signal5': ('weewx_signal_strength_5', 'Signal Strength for Sensor 5'),
    'signal6': ('weewx_signal_strength_6', 'Signal Strength for Sensor 6'),
    'signal7': ('weewx_signal_strength_7', 'Signal Strength for Sensor 7'),
    'signal8': ('weewx_signal_strength_8', 'Signal Strength for Sensor 8'),
    'snowBatteryStatus': ('weewx_snow_battery_status', 'Snow Battery Status'),
    'snowDepth': ('weewx_snow_depth', 'Snow Depth (in/cm)'),
    'snowMoisture': ('weewx_snow_moisture', 'Snow Moisture (%)'),
    'snowRate': ('weewx_snow_rate', 'Snow Rate (in/hr or cm/hr)'),
    'so2': ('weewx_sulfur_dioxide', 'Sulfur Dioxide (ppb)'),
    'soilLeafBatteryStatus': ('weewx_soil_leaf_battery_status', 'Battery status for the soil/leaf station (0: Ok, 1: Low)'),
    'soilMoist1': ('weewx_soil_moisture_1', 'Soil moisture for sensor 1 in centibars'),
    'soilMoist2': ('weewx_soil_moisture_2', 'Soil moisture for sensor 2 in centibars'),
    'soilMoist3': ('weewx_soil_moisture_3', 'Soil moisture for sensor 3 in centibars'),
    'soilMoist4': ('weewx_soil_moisture_4', 'Soil moisture for sensor 4 in centibars'),
    'soilTemp1': ('weewx_soil_temperature_1', 'Soil temperature for sensor 1 (°F/°C)'),
    'soilTemp2': ('weewx_soil_temperature_2', 'Soil temperature for sensor 2 (°F/°C)'),
    'soilTemp3': ('weewx_soil_temperature_3', 'Soil temperature for sensor 3 (°F/°C)'),
    'soilTemp4': ('weewx_soil_temperature_4', 'Soil temperature for sensor 4 (°F/°C)'),
    'sunshine': ('weewx_sunshine', 'Sunshine in minutes'),
    'supplyVoltage': ('weewx_supply_voltage', 'Supply voltage in volts'),
    'txBatteryStatus': ('weewx_tx_battery_status', 'Battery status for the transmitter (0: Ok, 1: Low)'),
    'usUnits': ('weewx_us_units', 'Units of measurement, 1 = US, 16 = METRIC, 17 = METRICWX'),
    'windBatteryStatus': ('weewx_wind_battery_status', 'Battery status for the wind sensor (0: Ok, 1: Low)'),
    'windDir': ('weewx_wind_direction', 'Wind direction in degrees'),
    'windGust': ('weewx_wind_gust', 'Wind gust speed in miles per hour or kilometers per hour'),
    'windGustDir': ('weewx_wind_gust_direction', 'Wind gust direction in degrees'),
    'windSpeed': ('weewx_wind_speed', 'Wind speed in miles per hour or kilometers per hour'),
    'windchill': ('weewx_windchill', 'Wind chill temperature (°F/°C)'),
    # fmt: on
}


# Create a WeeWX service class to update the gauges
class PrometheusService(weewx.engine.StdService):
    def __init__(self, engine, config_dict):
        super(PrometheusService, self).__init__(engine, config_dict)
        self.bind(weewx.NEW_LOOP_PACKET, self.new_loop_packet)
        # Create a new registry for this exporter
        self.registry = CollectorRegistry()
        # Create a dictionary map WeeWX metrics to Prometheus metrics
        self.prom_gauges = {}
        # Start the prometheus exporter
        start_http_server(8000, registry=self.registry)

    def new_loop_packet(self, event):
        packet = event.packet
        # For each metric in the packet, create or update the gauge
        for weewx_name, value in packet.items():
            if value is None:
                continue
            if weewx_name in WEEWX_TO_PROMETHEUS_MAPPING:
                prom_name, description = WEEWX_TO_PROMETHEUS_MAPPING[weewx_name]
                if prom_name not in self.prom_gauges:
                    # Create the gauge if it doesn't exist
                    gauge = Gauge(prom_name, description, registry=self.registry)
                    self.prom_gauges[prom_name] = gauge
                else:
                    # Update the gauge with the new value
                    gauge = self.prom_gauges[prom_name]
                gauge.set(value)
            else:
                log.warning(
                    f"Encountered unmapped WeeWX metric '{weewx_name}'. Please add a mapping in WEEWX_TO_PROMETHEUS_MAPPING."
                )
