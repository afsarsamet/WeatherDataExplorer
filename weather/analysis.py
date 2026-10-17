from statistics import mean


class WeatherAnalyzer:
    def __init__(self, station):
        self.station = station

    def average_temperature(self):
        return mean(m.tavg for m in self.station.measurements)

    def hottest_day(self):
        return max(self.station.measurements, key=lambda m: m.tmax)

    def coldest_day(self):
        return min(self.station.measurements, key=lambda m: m.tmin)
