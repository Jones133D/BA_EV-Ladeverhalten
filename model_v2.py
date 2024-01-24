import numpy as np
import matplotlib.pyplot as plt
# from matplotlib.dates import DateFormatter
import matplotlib.dates as mdates
import pandas as pd
import json
# from os import listdir
import random
from scipy import stats

# globals
num_rejected_cars = 0  # Anzahl abgewiesener EVs, wenn alle Ladesäulen belegt
total_number_cars = 0  # Anzahl ankommender EVs pro Tag
num_loaded_cars = 0  # Anzahl EVs mit Ladevorgang
minute_counter = 0
poisson_list = []
settings = []


class Model:
    def __init__(self, name, capacity):
        self.name = name
        self.capacity = float(capacity)
        # self.charging_curve = pd.read_csv(f'cars/{self.name}', sep=';', decimal=',', names=["soc", "power"])
        self.charging_curve = pd.read_parquet(f'cars/{self.name}.parquet')


class Car:
    def __init__(self, model, total_parking_duration, soc_begin):
        # self.is_EV = True
        self.model = model
        self.total_parking_duration = total_parking_duration
        self.consumed_energy = 0
        self.current_parking_duration = 0
        self.soc = float(soc_begin_generate(soc_begin))

    def charge(self):
        idx = self.soc / 0.25
        if idx < 0:
            idx = 0
        elif idx > 400:
            idx = 400

        power = float(self.model.charging_curve["power"].iloc[int(idx)])

        if power >= int(settings["max_power_per_station"]):
            power = int(settings["max_power_per_station"])

        if self.soc >= 100:
            ready_loaded = True
            power = float(0)
        else:
            ready_loaded = False

        energy = power / 60  # Energie, die in der Minute dazukommt (in Kilowatt-Minuten)
        self.soc += energy / self.model.capacity * 100  # Umrechnung in % soc der Gesamtkapazität
        self.consumed_energy += energy  # dazugekommene Energie dazu addieren
        return power, ready_loaded


def rand_new_car():
    global minute_counter
    global poisson_list
    if len(poisson_list) == 0:
        rng = np.random.default_rng()
        poisson_list = rng.poisson((settings["arriving_process_poisson_lambda"] / 60), size=1441)

    if settings["arriving_process"] == "random":
        random_choice = random.choices([0, 1], weights=(60, settings["arriving_process_rand_factor"]), k=1)
        if random_choice[0]:
            return 1
        else:
            return 0
    elif settings["arriving_process"] == "poisson":
        # random_choice = np.random.poisson((settings["arriving_process_poisson_lambda"] / 60))
        random_choice = poisson_list[minute_counter]
        return random_choice


def soc_begin_generate(soc_begin):
    if soc_begin == "equally_distributed":
        soc = random.randint(*settings["soc_begin_normal_distributed_between"])
    elif soc_begin == "gauss":
        soc = np.random.normal(((settings["soc_gauss_bis"] - settings["soc_gauss_von"]) / 2),
                               settings["soc_gauss_sigma"], 1)
        soc = np.clip(soc, settings["soc_gauss_von"], settings["soc_gauss_bis"])
    else:
        soc = 0
    print("soc_begin: ", soc_begin, ",", soc)
    return soc


class Parking:

    def __init__(self, number_of_stations, stations_max_power):
        self.number_of_stations = number_of_stations
        # self.stations_max_power = stations_max_power
        self.charging_cars = []

    def add_car(self, car):
        global num_rejected_cars
        global total_number_cars
        total_number_cars += 1

        if len(self.charging_cars) < self.number_of_stations:
            self.charging_cars.append(car)
        else:
            num_rejected_cars += 1
            print("Alle Ladesäulen belegt. Abgewiesene EVs: ", num_rejected_cars)

    def remove_ready_cars(self):
        global num_loaded_cars
        ready_cars = []
        for car in self.charging_cars:
            if car.current_parking_duration >= car.total_parking_duration:
                ready_cars.append(car)
        for car in ready_cars:
            num_loaded_cars += 1
            self.charging_cars.remove(car)
            # print(f"'{car.model.name}' charged {car.consumed_energy}kWh to {car.soc}%. Anzahl geladener EVs: {num_loaded_cars}")
            print(f"'{car.model.name}' charged %5.2f" % car.consumed_energy, "kWh to %5.2f" % car.soc, "% SOC")


# Example usage
def simulation(settings_selection):
    global num_rejected_cars
    global num_loaded_cars
    global settings
    global minute_counter
    num_rejected_cars = 0

    with open(settings_selection, "r") as f:
        settings = json.load(f)

    # Initialize models
    model1 = Model("VW_ID3_Pure_45kWh", 58)
    model2 = Model("Tesla_Model3_LR", 82.5)
    model3 = Model("2021_FIAT_500e_Hatchback", 42)
    model4 = Model("dummy100kW", 100)
    model5 = Model("Tesla_Model_SX_LR", 100)
    model6 = Model("Porsche_Taycan", 93.4)
    model7 = Model("Hyundai_KONA_64kWh", 64)
    model8 = Model("Hyundai_IONIQ5_LongRange", 72.6)
    model9 = Model("Tesla_ModelY", 82)
    model_list_all = [model1, model2, model3, model4, model5, model6, model7, model8, model9]  # Liste aller möglicher Modelle
    model_list = []  # Liste mit Modellen aus Settings.json
    for name in (settings["list_of_cars"]):
        for objekt in model_list_all:
            if name == objekt.name:
                model_list.append(objekt)

    # Initialize parking
    parking = Parking(int(settings["number_of_stations"]), int(settings["max_power_per_station"]))

    df_results = pd.DataFrame()  # Dataframe mit timecode und den Ergebnissen
    df_results.index = pd.date_range(start='20.02.2023 00:00:00', end='21.02.2023 00:00:00', freq='Min')

    if 'power_per_minute' not in df_results.columns:
        df_results['power_per_minute'] = 0

    if 'number_cars_charging' not in df_results.columns:
        df_results['number_cars_charging'] = 0

    # Simulate charging process
    for row_index in df_results.iterrows():
        # Generate random number of new cars
        num_new_cars = rand_new_car()
        for _ in range(num_new_cars):
            car_model = random.choice(model_list)
            # car_model = model4  # zum test nur bestimmtes Model laden
            #total_parking_duration = random.randint(*settings["parking_duration"])  # Parkdauer aus Settings
            total_parking_duration = int(stats.exponweib.rvs(settings["a_out"], settings["kappa_out"], \
                                                         loc=settings["loc_out"], scale=settings["lambda_out"], size=1))
            while (total_parking_duration <= 0):
                total_parking_duration = int(stats.exponweib.rvs(settings["a_out"], settings["kappa_out"], \
                                                                 loc=settings["loc_out"], scale=settings["lambda_out"],
                                                                 size=1))
            new_car = Car(car_model, total_parking_duration, settings["soc_begin"])
            parking.add_car(new_car)

        # Charge cars and remove ready cars
        for car in parking.charging_cars:
            power, ready_loaded = car.charge()
            # df_results['power_per_minute'] = df_results['power_per_minute'] + power
            # df_results['power_per_minute'] = power
            df_results.loc[row_index[0], 'power_per_minute'] += power

            car.current_parking_duration += 1
            # if ready_loaded:
            parking.remove_ready_cars()

            df_results.loc[row_index[0], 'number_cars_charging'] = parking.charging_cars.__len__()

            # df_results['power_summed'] = df_results['power_per_minute'].consum()
        minute_counter += 1

    print("Anzahl geladener EVs: ", num_loaded_cars)
    print("Abgewiesene EVs: ", num_rejected_cars)
    #return df_results, (num_rejected_cars + num_loaded_cars), num_rejected_cars
    return df_results


def plot(df):
    # Create figure with secondary y-axis
    fig1, ax1 = plt.subplots()
    fig1.set_size_inches(18.5, 10.5)
    color = 'tab:blue'
    ax1.set_xlabel('datetime')
    ax1.set_ylabel('power in kW', color=color)
    ax1.plot(np.asarray(df.index), np.asarray(df['power_per_minute']), c=color, alpha=0.6)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:orange'
    ax2.set_ylabel('number of cars', color=color)  # we already handled the x-label with ax1
    ax2.plot(np.asarray(df.index), np.asarray(df['number_cars_charging']), c=color, alpha=0.6)
    ax2.tick_params(axis='y', labelcolor=color)
    # ax2.set_ylim(0, settings["number_of_stations"])

    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))

    plt.xticks(rotation=45)

    # fig.autofmt_xdate()
    # date_form = mdates.DateFormatter("%H:%M")
    # ax1.xaxis.set_major_formatter(date_form)

    # df_results.plot()
    fig1.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.title(label='Lastverlauf')
    plt.show()

    # Histogramm Lastverteilung
    plt.hist(np.asarray(df['power_per_minute']), bins=40)
    # plt.hist(np.asarray(df['number_cars_charging']), bins=[0, 1, 2, 3, 4])
    plt.ylabel('Minuten')
    plt.xlabel('Load in kW')
    plt.title(label='Histogramm Load')
    plt.show()

    # CFD Plot
    """plt.hist(np.asarray(df['power_per_minute']), cumulative=True, label='CDF',
             histtype='step', alpha=0.8, color='k')
    plt.show()"""


def auswertung(df):
    max_values = df.power_per_minute.max()
    print("Maximale Last: ", max_values, "kWh")
    abs_over_60 = (df.power_per_minute > 0.6 * max_values).sum()
    percent_over_60 = (abs_over_60 / len(df.power_per_minute)) * 100
    abs_over_70 = (df.power_per_minute > 0.7 * max_values).sum()
    percent_over_70 = (abs_over_70 / len(df.power_per_minute)) * 100
    abs_over_80 = (df.power_per_minute > 0.8 * max_values).sum()
    percent_over_80 = (abs_over_80 / len(df.power_per_minute)) * 100
    abs_over_90 = (df.power_per_minute > 0.9 * max_values).sum()
    percent_over_90 = (abs_over_90 / len(df.power_per_minute)) * 100
    abs_over_95 = (df.power_per_minute > 0.95 * max_values).sum()
    percent_over_95 = (abs_over_95 / len(df.power_per_minute)) * 100
    print("Minuten über 60%% der maximalen Last (%5.2f" % (0.60 * max_values), "kWh):", abs_over_60, "Entsprechen",
          "%5.2f" % percent_over_60, "%")
    print("Minuten über 70%% der maximalen Last (%5.2f" % (0.70 * max_values), "kWh):", abs_over_70, "Entsprechen",
          "%5.2f" % percent_over_70, "%")
    print("Minuten über 80%% der maximalen Last (%5.2f" % (0.80 * max_values), "kWh):", abs_over_80, "Entsprechen",
          "%5.2f" % percent_over_80, "%")
    print("Minuten über 90%% der maximalen Last (%5.2f" % (0.90 * max_values), "kWh):", abs_over_90, "Entsprechen",
          "%5.2f" % percent_over_90, "%")
    print("Minuten über 95%% der maximalen Last (%5.2f" % (0.95 * max_values), "kWh):", abs_over_95, "Entsprechen",
          "%5.2f" % percent_over_95, "%")
    return


def main():
    # df_results_returned = simulation("settings_model_charging-time.json")
    df_results_returned = simulation("settings_soc_begin.json")
    plot(df_results_returned)


if __name__ == "__main__":
    main()
