import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import json
from os import listdir
import random

with open("settings.json") as f:
    settings = json.load(f)


class Model:
    def __init__(self, name, capacity):
        self.name = name
        self.capacity = capacity
        # self.charging_curve = pd.read_csv(f'cars/{self.name}', sep=';', decimal=',', names=["soc", "power"])
        self.charging_curve = pd.read_parquet(f'cars/{self.name}.parquet')


class Car:
    def __init__(self, model, total_parking_duration):
        self.is_EV = True
        self.model = model
        self.total_parking_duration = total_parking_duration
        self.soc = 0
        self.consumed_energy = 0
        self.current_parking_duration = 0

    def charge(self):
        # print(self.model.charging_curve.info())
        idx = self.soc / 0.25
        # wenn unterhalb der Ladekurve, ersten Index benutzen
        if idx <= self.model.charging_curve.index.stop - 1:
            power = float(self.model.charging_curve["power"].iloc[int(idx)])
        else:
            # wenn oberhalb der Ladekurve, letzten Index benutzen
            power = float(self.model.charging_curve["power"].iloc[self.model.charging_curve.index.stop - 1])
        energy = power / 60
        self.soc += energy / self.model.capacity * 100
        if self.soc >= 100:
            ready = True
        else:
            ready = False

        self.consumed_energy += energy
        return power, ready


def rand_new_car(weight):
    random_choice = random.choices([0, 1], weights=(100, weight), k=1)
    if random_choice[0]:
        return 1
    else:
        return 0


class Parking:

    def __init__(self, number_of_stations, stations_max_power):
        self.number_of_stations = number_of_stations
        self.stations_max_power = stations_max_power
        self.charging_cars = []

    def add_car(self, car):
        if len(self.charging_cars) < self.number_of_stations:
            self.charging_cars.append(car)
        else:
            print("Alle Ladesäulen belegt. Abgewiesene EVs: ")

    def remove_ready_cars(self):
        ready_cars = []
        for car in self.charging_cars:
            if car.current_parking_duration >= car.total_parking_duration:
                ready_cars.append(car)
        for car in ready_cars:
            self.charging_cars.remove(car)
            print(f"Car with model '{car.model.name}' is fully charged and leaving the parking.")


# Example usage
def main():
    # Initialize models
    model1 = Model("VW_ID3_Pure", 100)
    model2 = Model("Tesla_Model_3_LR", 120)
    model3 = Model("FIAT_500e_Hatchback_2021", 110)

    # Initialize parking
    # parking = Parking(int("number_of_stations"), int("max_power_per_station")
    parking = Parking(4, 50)

    df_results = pd.DataFrame()  # Dataframe mit timecode und den Ergebnissen
    df_results.index = pd.date_range(start='20.02.2023 00:00:00', end='21.02.2023 00:00:00', freq='Min')

    if 'power_per_minute' not in df_results.columns:
        df_results['power_per_minute'] = 0

    if 'number_cars_charging' not in df_results.columns:
        df_results['number_cars_charging'] = 0

    # Simulate charging process
    # for minute in range(1, 61):
    #   print(f"Minute: {minute}")
    for row_index in df_results.iterrows():
        # Generate random number of new cars
        # num_new_cars = random.randint(0, 1)
        num_new_cars = rand_new_car(5)
        for _ in range(num_new_cars):
            car_model = random.choice([model1, model2, model3])
            car_model = model1  # Testweise nur model1 (VW ID3) laden
            total_parking_duration = random.randint(*settings["parking_duration"])
            new_car = Car(car_model, total_parking_duration)
            parking.add_car(new_car)

        # Charge cars and remove ready cars
        for car in parking.charging_cars:
            power, ready = car.charge()
            # df_results['power_per_minute'] = df_results['power_per_minute'] + power
            # df_results['power_per_minute'] = power
            df_results.loc[row_index[0], 'power_per_minute'] += power

            car.current_parking_duration += 1
            if ready:
                parking.remove_ready_cars()

            df_results.loc[row_index[0], 'number_cars_charging'] = parking.charging_cars.__len__()

            # df_results['power_summed'] = df_results['power_per_minute'].consum()
    # plot df_results

    """fig, ax1 = plt.subplots()
    color = 'tab:blue'
    ax1.set_xlabel('power in kW')
    ax1.set_ylabel('datetime', color=color)
    ax1.plot(df_results[row_index[0]], color=color)
    ax1.tick_params(axis='y', labelcolor=color)"""

    df_results.plot()
    plt.show()


if __name__ == "__main__":
    main()
