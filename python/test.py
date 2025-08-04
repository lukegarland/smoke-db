import time
import prometheus
import random
import pprint
prometheus_exporter = prometheus.PrometheusExporter()
NUM_PROBES = 4

def main():
    predictor = prometheus.TemperatureTimePredictor(prometheus_exporter)

    temperatures = {
        1: 25,
        2: 50,
        3: 65,
        4: 75
    }
    while True:

        for probe_num, temperature in temperatures.items():
            
            new_temp_delta = random.normalvariate(mu=2, sigma=1)
            temperature = round(temperature + new_temp_delta,3)
            prometheus_exporter.report_probe_temp(temperature, probe_num)
            temperatures[probe_num] = temperature
            predictor.run_realtime_prediction()
            
        pprint.pprint(temperatures)
        time.sleep(10)
    pass

if __name__ == "__main__":
    main()