import prometheus_client
import prometheus_api_client

import datetime
import numpy as np
import time

def c_to_f(celsius_reading:float, round_to=2) -> float:
    return round(celsius_reading*9/5+32, round_to)

class PrometheusExporter():

    def __init__(self, port=8000):
        self.probe_temperature_celsius = prometheus_client.Gauge("probe_temperature_celsius", "The temperature read by the probe in Celsius", labelnames=['probe_num'])
        self.probe_temperature_fahrenheit = prometheus_client.Gauge("probe_temperature_fahrenheit", "The temperature read by the probe in Fahrenheit", labelnames=['probe_num'])
        
        self.probe_prediction_time_to_temp_timestamp = prometheus_client.Gauge("probe_prediction_time_to_temp_timestamp", 
                                                                    "The predicted timestamp when the probe reaches target_temp, based on linear regression", 
                                                                    labelnames=['probe_num', 'target_temp'])
        
        prometheus_client.start_http_server(port)

    def report_probe_temp(self, celsius_reading, probe_num):
        if celsius_reading is None:
            celsius_reading = float("NaN")
        self.probe_temperature_celsius.labels(probe_num=probe_num).set(celsius_reading)
        self.probe_temperature_fahrenheit.labels(probe_num=probe_num).set(c_to_f(celsius_reading))
    

    def probe_disconnected(self):
        for probe in self.probe_temperature_celsius._labelvalues:
            self.probe_temperature_celsius.labels(probe_num=probe).set="NaN"
            self.probe_temperature_fahrenheit.labels(probe_num=probe).set="NaN"

    def report_predictions(self, probe_num, target_temp, timestamp_to_temp):
        self.probe_prediction_time_to_temp_timestamp.labels(probe_num=probe_num, target_temp=target_temp).set(timestamp_to_temp)


class TemperatureTimePredictor():

    
    def __init__(self, prometheus_exporter: PrometheusExporter):
        self.exporter = prometheus_exporter
        self.api = prometheus_api_client.prometheus_connect.PrometheusConnect(url="http://localhost:9090")
        self.temperature_metric = "probe_temperature_fahrenheit"
    
        # normal meat teamperature ranges are 100 to 205 F
        # normal smoking temperature ranges are 180 to 400 F
        self.temperature_predictions = [i for i in range(100, 205+1, 5)] + [i for i in range(225, 400+1, 25)]

    def get_temperature_data(self, start, end):
        
        data = self.api.custom_query_range(f"{self.temperature_metric}", start_time=start, end_time=end, step="15s")
        
        # {'probe_num': np.ndarray}
        formatted_data = {}
        for result in data:
            probe_num = result['metric'].get('probe_num')
            if probe_num:
                formatted_data[probe_num] = np.array(result['values'], 'float64')
        return formatted_data
        

    def predict_time_to_temperature(self, array:np.ndarray, target_temp:float=165):
        x = array[:, 0]
        y = array[:, 1]
        
        # degree 1 is linear
        poly_fit_coeff = np.polyfit(x, y, deg=1)
        m = poly_fit_coeff[0]
        b = poly_fit_coeff[1]

        # y = mx+b, so...
        # x = (y-b)/m
        predicted_timestamp = round((target_temp - b)/m, 1)
        return predicted_timestamp
    

    def run_prediction(self, prediction_time:datetime.datetime, prediction_lookback_duration:datetime.timedelta, target_temp):
        window_end = prediction_time
        window_start = window_end - prediction_lookback_duration
        temperature_data = self.get_temperature_data(window_start, window_end)
        
        results = {}

        for probe, temperature_array in temperature_data.items():
            predicted_timestamp = self.predict_time_to_temperature(temperature_array, target_temp)
            results[probe] = predicted_timestamp
        return results
    
    def run_realtime_prediction(self, prediction_lookback_duration:datetime.timedelta=datetime.timedelta(minutes=2)):
        for target_temp in self.temperature_predictions:
            predictions = self.run_prediction(datetime.datetime.now(), prediction_lookback_duration, target_temp)
            
            for probe_num, prediction_timestamp in predictions.items():
                
                # set timestamp to zero if time has already passed. 
                if prediction_timestamp < time.time():
                    prediction_timestamp = 0

                self.exporter.report_predictions(probe_num, target_temp, prediction_timestamp)


if __name__ == "__main__":
    from pprint import pprint
    exporter = PrometheusExporter()
    predictor = TemperatureTimePredictor(exporter)

    end_date = datetime.datetime(2025, 8, 2, 18, 50, 00)
    start_date = end_date - datetime.timedelta(minutes=5)
    formatted_data = predictor.get_temperature_data(start_date, end_date)
    
    pprint(predictor.predict_time_to_temperature(formatted_data.get('1')))
    pprint(predictor.predict_time_to_temperature(formatted_data.get('2')))
    pprint(predictor.predict_time_to_temperature(formatted_data.get('3')))
    pprint(predictor.predict_time_to_temperature(formatted_data.get('4')))