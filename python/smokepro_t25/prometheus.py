import prometheus_client


def c_to_f(celsius_reading:float, round_to=2) -> float:
    return round(celsius_reading*9/5+32, round_to)


class PrometheusExporter():

    def __init__(self):
        self.probe_temperature_celsius = prometheus_client.Gauge("probe_temperature_celsius", "The temperature read by the probe in Celsius", labelnames=['probe_num'])
        self.probe_temperature_fahrenheit = prometheus_client.Gauge("probe_temperature_fahrenheit", "The temperature read by the probe in Fahrenheit", labelnames=['probe_num'])
        prometheus_client.start_http_server(8000)

    def report_probe_temp(self, celsius_reading, probe_num):
        if celsius_reading is None:
            celsius_reading = float("NaN")
        self.probe_temperature_celsius.labels(probe_num=probe_num).set(celsius_reading)
        self.probe_temperature_fahrenheit.labels(probe_num=probe_num).set(c_to_f(celsius_reading))
    

    def probe_disconnected(self):
        for probe in self.probe_temperature_celsius._labelvalues:
            self.probe_temperature_celsius.labels(probe_num=probe).set="NaN"
            self.probe_temperature_fahrenheit.labels(probe_num=probe).set="NaN"
