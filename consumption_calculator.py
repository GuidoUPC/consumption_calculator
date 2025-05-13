
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.table
import numpy as np
import pandas as pd
import math
import random
from IPython.display import display

class Sensor:
    def __init__(self, name, operating_voltage, active_consumption, inactive_consumption, sampling_rate, active_time, data_volume):
        self.name = name
        self.operating_voltage = operating_voltage
        self.active_consumption = active_consumption
        self.inactive_consumption = inactive_consumption
        self.sampling_rate = sampling_rate # in Hz. Number of measurements per second
        self.active_time = active_time # in seconds. Time needed to take the measurement
        self.data_volume = data_volume # in bytes/sampling

    def __repr__(self):
        return (f"Sensor(name={self.name}, "
                f"operating_voltage={self.operating_voltage}, "
                f"active_consumption={self.active_consumption}, "
                f"inactive_consumption={self.inactive_consumption}, "
                f"sampling_rate={self.sampling_rate}, "
                f"active_time={self.active_time}, "
                f"data_volume={self.data_volume})")
    
    def get_name(self):
        return self.name


class Microcontroller:
    def __init__(self, name, operating_voltage, active_consumption, light_sleep_consumption, deep_sleep_consumption):
        self.name = name
        self.operating_voltage = operating_voltage
        self.active_consumption = active_consumption # Changes depending on the microcontroller's clock frequency
        self.light_sleep_consumption = light_sleep_consumption
        self.deep_sleep_consumption = deep_sleep_consumption

    def __repr__(self):
        return (f"Microcontroller(name={self.name}, "
                f"operating_voltage={self.operating_voltage}, "
                f"active_consumption={self.active_consumption}, "
                f"light_sleep_consumption={self.light_sleep_consumption}, "
                f"deep_sleep_consumption={self.deep_sleep_consumption})")


class RadioInterface:
    def __init__(self, name, operating_voltage, transmit_consumption, receive_consumption, inactive_consumption, datarate, data_refresh_rate):
        self.name = name
        self.operating_voltage = operating_voltage
        self.transmit_consumption = transmit_consumption
        self.receive_consumption = receive_consumption
        self.inactive_consumption = inactive_consumption
        self.datarate = datarate
        self.data_refresh_rate = data_refresh_rate

    def __repr__(self):
        return (f"RadioInterface(name={self.name}, "
                f"operating_voltage={self.operating_voltage}, "
                f"transmit_consumption={self.transmit_consumption}, "
                f"receive_consumption={self.receive_consumption}, "
                f"inactive_consumption={self.inactive_consumption}, "
                f"datarate={self.datarate}, "
                f"data_refresh_rate={self.data_refresh_rate})")
    
class SystemConsumtion:
    def __init__(self, sensoring_consumption, communications_consumption, microcontroller_consumption):
        self.sensoring_consumption = sensoring_consumption
        self.communications_consumption = communications_consumption
        self.microcontroller_consumption = microcontroller_consumption
    def __repr__(self):
        return (f"SystemConsumtion(sensoring_consumption={self.sensoring_consumption}, "
                f"communications_consumption={self.communications_consumption}, "
                f"microcontroller_consumption={self.microcontroller_consumption})")
    def set_sensoring_consumption(self, sensoring_consumption):
        self.sensoring_consumption = sensoring_consumption
    def set_communications_consumption(self, communications_consumption):
        self.communications_consumption = communications_consumption
    def set_microcontroller_consumption(self, microcontroller_consumption):
        self.microcontroller_consumption = microcontroller_consumption
    def get_sensoring_consumption(self):
        return self.sensoring_consumption
    def get_communications_consumption(self):
        return self.communications_consumption
    def get_microcontroller_consumption(self):
        return self.microcontroller_consumption
    def get_sensoring_current_consumption(self):
        return sum(sensor.get_total_energy() for sensor in self.sensoring_consumption)
    def get_sensors_current_consumption(self):
        return [sensor.get_total_energy() for sensor in self.sensoring_consumption]
    def get_communications_energy_consumption(self):
        return self.communications_consumption.get_total_energy()
    def get_microcontroller_energy_consumption(self):
        return self.microcontroller_consumption.get_total_energy()
    def get_total_energy(self):
        total_sensoring_consumption = sum(sensor.get_total_energy() for sensor in self.sensoring_consumption)
        return total_sensoring_consumption + self.communications_consumption.get_total_energy() + self.microcontroller_consumption.get_total_energy()
    
class ElementConsumption:
    def __init__(self, name, operating_voltage, active_energy, inactive_energy, schedule):
        self.name = name
        self.operating_voltage = operating_voltage
        self.schedule = schedule
        self.active_energy = active_energy
        self.inactive_energy = inactive_energy
    def __repr__(self):
        return (f"SensoringConsumption(active_energy={self.active_energy}, "
                f"inactive_energy={self.inactive_energy})")
    def set_active_energy(self, active_energy):
        self.active_energy = active_energy
    def set_inactive_energy(self, inactive_energy):
        self.inactive_energy = inactive_energy
    def get_active_energy(self):
        return self.active_energy
    def get_inactive_energy(self):
        return self.inactive_energy
    def get_total_energy(self):
        return self.active_energy + self.inactive_energy

def get_system_energy_consumption(sensors, microcontroller, radio_interface, duration):
    total_energy = 0
    data_vloume = 0
    measuring_time = 0
    first_measure_time = 0
    resolution = 1 # Number of samples per second
    num_samples = duration * resolution
    # Create a time array
    time = np.linspace(0, num_samples, num_samples+1) # Time in seconds
    # Calculate energy consumption for sensors
    sensoring_consumptions = []
    for sensor in sensors:
        sensor_schedule = [False]*num_samples
        # Calculate the number of measures
        number_of_measures = sensor.sampling_rate * duration
        measure_period = duration / number_of_measures
        for i in range(math.ceil(number_of_measures)):
            # Calculate the start time of the measure i
            start_measure_time = first_measure_time + measure_period * i
            if start_measure_time > duration:
                break
            end_measure_time = start_measure_time + sensor.active_time
            if start_measure_time > duration:
                break
            if end_measure_time > duration:
                end_measure_time = duration
            sensor_schedule[int(start_measure_time)*resolution:int(end_measure_time)*resolution] = [True]*int((end_measure_time - start_measure_time)*resolution)
        first_measure_time += sensor.active_time
        measuring_time += sensor.active_time * number_of_measures # Measures could be parallelized depending on the available ports and maximum current supply
        active_energy = sensor.active_consumption * measuring_time
        inactive_energy = sensor.inactive_consumption * (duration - measuring_time)
        sensoring_consumptions.append(ElementConsumption(sensor.get_name(), sensor.operating_voltage, active_energy, inactive_energy, sensor_schedule))
        data_vloume += sensor.data_volume * number_of_measures

    # Calculate energy consumption for radio interface
    radio_schedule = [False]*num_samples
    # Calculate the number of transmissions
    number_of_transmissions = math.ceil(duration * radio_interface.data_refresh_rate)
    # Calculate the transmission period
    transmission_period = 1 / radio_interface.data_refresh_rate
    # Calculate the time of each transmission
    transmission_time = data_vloume*8 / radio_interface.datarate
    for transmission in np.linspace(1, number_of_transmissions, number_of_transmissions):
        end_transmission_time = transmission_period*transmission
        start_transmission_time = end_transmission_time - transmission_time
        if start_transmission_time > duration:
            break
        if end_transmission_time > duration:
            end_transmission_time = duration
        radio_schedule[int(start_transmission_time)*resolution:int(end_transmission_time)*resolution] = [True]*int((end_transmission_time - start_transmission_time)*resolution+1)
    # Calculate the active time of the radio interface
    radio_active_time = transmission_time * number_of_transmissions
    if radio_active_time > duration:
        radio_active_time = duration
    inactive_comm_energy = radio_interface.inactive_consumption * (duration - radio_active_time)
    active_comm_energy = radio_interface.transmit_consumption * radio_active_time
    comm_consumtion = ElementConsumption(radio_interface.name, radio_interface.operating_voltage, active_comm_energy, inactive_comm_energy, radio_schedule)

    # Calculate energy consumption for microcontroller
    microcontroller_active_time = measuring_time + radio_active_time
    if microcontroller_active_time > duration:
        microcontroller_active_time = duration
    microcontroller_active_energy = microcontroller.active_consumption * microcontroller_active_time
    microcontroller_inactive_energy = microcontroller.deep_sleep_consumption * (duration - microcontroller_active_time)
    # Microcontroller is active when sensoring is active or when the radio interface is active
    # Sensoring is active when some sensor is active
    sensoring_schedule = [False] * len(time)
    for sensor in sensoring_consumptions:
        sensoring_schedule = [sensor_is_active or sensoring_is_active for sensor_is_active, sensoring_is_active in zip(sensor.schedule, sensoring_schedule)]
    microcontroller_schedule = [sensoring_is_active or radio_is_active for sensoring_is_active, radio_is_active in zip(sensoring_schedule, radio_schedule)]
    microcontroller_consumption = ElementConsumption(microcontroller.name, microcontroller.operating_voltage, microcontroller_active_energy, microcontroller_inactive_energy, microcontroller_schedule)
    return SystemConsumtion(sensoring_consumptions, comm_consumtion, microcontroller_consumption)

def get_user_input():
    while True:
        choice = input("Do you want to enter a Sensor, Microcontroller, or RadioInterface? (Enter 'exit' to quit): ").strip().lower()
        if choice == 'sensor':
            sensor_name = input("Enter sensor name: ")
            operating_voltage = float(input("Enter operating voltage (V): "))
            active_consumption = float(input("Enter active consumption (mA): "))
            inactive_consumption = float(input("Enter inactive consumption (mA): "))
            sampling_rate = float(input("Enter sampling rate (Hz): "))
            active_time = float(input("Enter active time (seconds): "))
            data_volume = float(input("Enter data volume (bytes/sampling): "))
            sensor = Sensor(sensor_name, operating_voltage, active_consumption, inactive_consumption, sampling_rate, active_time, data_volume)
            with open("sensors.txt", "a") as file:
                file.write(str(sensor) + "\n")
        elif choice == 'microcontroller':
            microcontroller_name = input("Enter microcontroller name: ")
            operating_voltage = float(input("Enter operating voltage (V): "))
            active_consumption = float(input("Enter active consumption (mA): "))
            light_sleep_consumption = float(input("Enter light sleep consumption (mA): "))
            deep_sleep_consumption = float(input("Enter deep sleep consumption (mA): "))
            microcontroller = Microcontroller(microcontroller_name, operating_voltage, active_consumption, light_sleep_consumption, deep_sleep_consumption)
            with open("microcontrollers.txt", "a") as file:
                file.write(str(microcontroller) + "\n")
        elif choice == 'radiointerface':
            radio_interface_name = input("Enter radio interface name: ")
            operating_voltage = float(input("Enter operating voltage (V): "))
            transmit_consumption = float(input("Enter transmit consumption (mA): "))
            receive_consumption = float(input("Enter receive consumption (mA): "))
            inactive_consumption = float(input("Enter inactive consumption (mA): "))
            datarate = float(input("Enter datarate (bps): "))
            data_refresh_rate = float(input("Enter data refresh rate: "))
            radio_interface = RadioInterface(radio_interface_name, operating_voltage, transmit_consumption, receive_consumption, inactive_consumption, datarate, data_refresh_rate)
            with open("radio_interfaces.txt", "a") as file:
                file.write(str(radio_interface) + "\n")
        elif choice == 'exit':
            break
        else:
            print("Invalid choice. Please enter 'Sensor', 'Microcontroller', 'RadioInterface', or 'exit'.")

def read_sensors():
    sensors = []
    with open("sensors.txt", "r") as file:
        all_sensors = file.readlines()
        for i, line in enumerate(all_sensors):
            print(f"{i}: {line.strip()}")
        sensor_indices = input("Enter the positions of the sensors to load (comma-separated): ").strip().split(",")
        sensor_indices = [int(index.strip()) for index in sensor_indices]
        for index in sensor_indices:
            line = all_sensors[index].strip()
            line = line.replace("Sensor(", "")
            line = line.replace(")", "")
            line = line.split(", ")
            sensors.append(Sensor(line[0].split("=")[1], float(line[1].split("=")[1]), float(line[2].split("=")[1]), float(line[3].split("=")[1]), float(line[4].split("=")[1]), float(line[5].split("=")[1]), float(line[6].split("=")[1])))
    return sensors

def read_microcontroller():
    with open("microcontrollers.txt", "r") as file:
        all_microcontrollers = file.readlines()
        for i, line in enumerate(all_microcontrollers):
            print(f"{i}: {line.strip()}")
        microcontroller_index = int(input("Enter the position of the microcontroller to load: ").strip())
        line = all_microcontrollers[microcontroller_index].strip()
        line = line.replace("Microcontroller(", "")
        line = line.replace(")", "")
        line = line.split(", ")
        microcontroller = Microcontroller(line[0].split("=")[1], float(line[1].split("=")[1]), float(line[2].split("=")[1]), float(line[3].split("=")[1]), float(line[4].split("=")[1]))
    return microcontroller

def read_radio_interface():
    with open("radio_interfaces.txt", "r") as file:
        all_radio_interfaces = file.readlines()
        for i, line in enumerate(all_radio_interfaces):
            print(f"{i}: {line.strip()}")
        radio_interface_index = int(input("Enter the position of the radio interface to load: ").strip())
        line = all_radio_interfaces[radio_interface_index].strip()
        line = line.replace("RadioInterface(", "")
        line = line.replace(")", "")
        line = line.split(", ")
        radio_interface = RadioInterface(line[0].split("=")[1], float(line[1].split("=")[1]), float(line[2].split("=")[1]), float(line[3].split("=")[1]), float(line[4].split("=")[1]), float(line[5].split("=")[1]), float(line[6].split("=")[1]))
    return radio_interface


def show_consumptions(system_consumption):
    # This method plots a pie chart with the energy consumption of each element in a fingure
    #  and another three figures for sensoring, communications and microcontroller energy consumption distinguishing between active and inactive consumption


    def slices_values_curr(value):
        return '{:.2f}%,\nAbs: {:.0f} mAs,\nAvg: {:.0f} mA'.format(100*value/total, value, value/duration)
    
    def slices_values_pwr(value):
        return '{:.2f}%,\nAbs: {:.0f} mWs,\nAvg: {:.0f} mW'.format(100*value/total, value, value/duration)
    
    def create_labels(widges, labels):
        bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
        kw = dict(arrowprops=dict(arrowstyle="-"),
                bbox=bbox_props, zorder=0, va="center")
        for i, p in enumerate(wedges):
            ang = (p.theta2 - p.theta1)/2. + p.theta1
            y = np.sin(np.deg2rad(ang))
            x = np.cos(np.deg2rad(ang))
            horizontalalignment = {-1: "right", 1: "left"}[int(np.sign(x))]
            connectionstyle = f"angle,angleA=0,angleB={ang}"
            kw["arrowprops"].update({"connectionstyle": connectionstyle})
            ax.annotate(curr_consumptions[i], xy=(x, y), xytext=((1.6-abs(y))*np.sign(x), 1.1*y),
                        horizontalalignment=horizontalalignment, **kw)
            
    plt.figure(figsize=(12, 8))
    # Display duration
    ax = plt.subplot(6, 1, 1)
    duration_table = matplotlib.table.table(
        ax,
        [[str(duration) + " seconds"]],
        colLabels=['Duration (s)'],
        cellLoc='center',
        loc='center',
        rowLabels=[''])
    duration_table.set_fontsize(8)
    duration_table.scale(1, 2)
    plt.axis('off')
    # Display the microcontroller table
    ax = plt.subplot(6, 1, 2)
    microcontroller_df = pd.DataFrame([vars(microcontroller)])
    microcontroller_table = matplotlib.table.table(
        ax,
        microcontroller_df[['name','operating_voltage', 'active_consumption', 'light_sleep_consumption', 'deep_sleep_consumption']].values,
        colLabels=['MC name', 'Voltage (V)', 'Active\nCurr. Cons. (mA)', 'Light Sleep\nCurr. Cons. (mA)', 'Deep Sleep\nCurr. Cons. (mA)'],
        # rowLabels=[microcontroller.name],
        # colWidths=[0.18]*5,
        colColours=['#f0f0f0']*5,
        cellLoc='center',
        loc='center')
    microcontroller_table.set_fontsize(8)
    microcontroller_table.scale(1, 2)
    plt.axis('off')
    # Display the radio interface table
    ax = plt.subplot(6, 1, 3)
    radio_interface_df = pd.DataFrame([vars(radio_interface)])
    radio_interface_table = matplotlib.table.table(
        ax,
        radio_interface_df[['name', 'operating_voltage', 'transmit_consumption', 'receive_consumption', 'inactive_consumption', 'datarate', 'data_refresh_rate']].values,
        colLabels=['Radio name', 'Voltage (V)', 'Transmit\nCurr. Cons. (mA)', 'Receive\nCurr. Cons. (mA)', 'Inactive\nCurr. Cons. (mA)', 'Datarate (bps)', 'Update Rate (Hz)'],
        # rowLabels=[radio_interface.name],
        # colWidths=[0.18]*7,
        colColours=['#f0f0f0']*7,
        cellLoc='center',
        loc='center')
    radio_interface_table.set_fontsize(8)
    radio_interface_table.scale(1, 2)
    plt.axis('off')
    # Display the sensors table
    ax = plt.subplot(6, 1, 4)
    sensors_df = pd.DataFrame([vars(sensor) for sensor in sensors])
    sensors_table = matplotlib.table.table(
        ax,
        sensors_df[['name','operating_voltage', 'active_consumption', 'inactive_consumption', 'sampling_rate', 'active_time', 'data_volume']].values,
        colLabels=['Sensor name', 'Voltage (V)', 'Active\nCurr. Cons. (mA)', 'Inactive\nCurr. Cons. (mA)', 'Sampling Rate (Hz)', 'Active Time (s)', 'Data\nVolume (bytes)'],
        # rowLabels=[sensor.get_name() for sensor in sensors],
        # colWidths=[0.2]*7,
        colColours=['#f0f0f0']*7,
        cellLoc='center',
        loc='center')
    sensors_table.set_fontsize(8)
    sensors_table.scale(1, 2)
    plt.axis('off')

    plt.figure(figsize=(12, 8))
    # Plot the sensoring energy consumption distinguishing between active and inactive consumption
    plt.subplot(1, 3, 1)
    plt.title("Sensoring Energy\nConsumption")
    sensoring_actticve_energy_consumption = 0
    sensoring_inactive_energy_consumption = 0
    for sensor in system_consumption.get_sensoring_consumption():
        sensoring_actticve_energy_consumption += sensor.get_active_energy()
        sensoring_inactive_energy_consumption += sensor.get_inactive_energy()
    labels = ['Active Consumption', 'Inactive Consumption']
    sizes = [sensoring_actticve_energy_consumption, sensoring_inactive_energy_consumption]
    colors = ['gold', 'lightcoral']
    explode = (0.1, 0)  # explode the first slice
    total = sensoring_inactive_energy_consumption + sensoring_actticve_energy_consumption
    wedges, texts, autotexts = plt.pie(sizes, explode=explode, colors=colors, autopct=slices_values_curr, shadow=True, startangle=140)
    plt.setp(autotexts, size=8, weight="bold")
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    # plt.table([["%.2f mAh" % (size/3600) for size in sizes]], loc='bottom', cellLoc='center', colLabels=['Active Consumption', 'Inactive Consumption'])
    
    # Plot the communications energy consumption distinguishing between active and inactive consumption
    plt.subplot(1, 3, 2)
    plt.title("Communications Energy\nConsumption")
    sizes = [system_consumption.get_communications_consumption().get_active_energy(), system_consumption.get_communications_consumption().get_inactive_energy()]
    explode = (0.1, 0)  # explode the first slice
    total = system_consumption.get_communications_energy_consumption()
    wedges, texts, autotexts = plt.pie(sizes, colors=colors, explode=explode, autopct=slices_values_curr, shadow=True, startangle=140)
    plt.legend(wedges, labels, loc="lower center" )
    plt.setp(autotexts, size=8, weight="bold")
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    # plt.table([["%.2f mAh" % (size/3600) for size in sizes]], loc='bottom', cellLoc='center', colLabels=['Active Consumption', 'Inactive Consumption'])
    
    # Plot the microcontroller energy consumption distinguishing between active and inactive consumption
    plt.subplot(1, 3, 3)
    plt.title("Microcontroller Energy\nConsumption")
    sizes = [system_consumption.get_microcontroller_consumption().get_active_energy(), system_consumption.get_microcontroller_consumption().get_inactive_energy()]
    total = system_consumption.get_microcontroller_energy_consumption()
    wedges, texts, autotexts = plt.pie(sizes, colors=colors, explode=explode, autopct=slices_values_curr, shadow=True, startangle=140)
    plt.setp(autotexts, size=8, weight="bold")
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
    # plt.table([["%.2f mAh" % (size/3600) for size in sizes]], loc='bottom', cellLoc='center', colLabels=['Active Consumption', 'Inactive Consumption'])
   
    plt.figure(figsize=(12, 8))
    
    # # Plot the current consumption of the system
    # ax = plt.subplot(2, 2, 1)
    # print(system_consumption.get_sensors_current_consumption())
    # sizes = [system_consumption.get_sensoring_current_consumption(), system_consumption.get_microcontroller_energy_consumption(), system_consumption.get_communications_energy_consumption()]
    # total = sum(sizes)
    # curr_consumptions = ["Sensors:\n" + slices_values_curr(system_consumption.get_sensoring_current_consumption()), "Microcontroller:\n" + slices_values_curr(system_consumption.get_microcontroller_energy_consumption()), "Radio Interface:\n" + slices_values_curr(system_consumption.get_communications_energy_consumption())]
    # wedges, texts = plt.pie(sizes, wedgeprops=dict(width=0.5), startangle=-80)
    # create_labels(wedges, curr_consumptions)
    # ax.set_title("Current Consumption")
    # plt.axis('equal')

    # Plot the current consumption of the system
    ax = plt.subplot(3, 2, 1)
    # sizes = [system_consumption.get_sensoring_current_consumption(), system_consumption.get_microcontroller_energy_consumption(), system_consumption.get_communications_energy_consumption()]
    sizes_curr = system_consumption.get_sensors_current_consumption()
    sizes_curr.extend([system_consumption.get_microcontroller_energy_consumption(), system_consumption.get_communications_energy_consumption()])
    total = sum(sizes_curr)
    colors = ["#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)])
             for i in range(len(sizes_curr))]
    curr_consumptions = [sensor.name + "\n" + slices_values_curr(sensor.get_total_energy()) for sensor in system_consumption.get_sensoring_consumption()]
    curr_consumptions.extend([system_consumption.get_microcontroller_consumption().name + ":\n" + slices_values_curr(system_consumption.get_microcontroller_energy_consumption()), system_consumption.get_communications_consumption().name + ":\n" + slices_values_pwr(system_consumption.get_communications_energy_consumption())])
    # curr_consumptions = ["Sensors:\n" + slices_values_curr(system_consumption.get_sensoring_current_consumption()), "Microcontroller:\n" + slices_values_curr(system_consumption.get_microcontroller_energy_consumption()), "Radio Interface:\n" + slices_values_curr(system_consumption.get_communications_energy_consumption())]
    wedges, texts = plt.pie(sizes_curr, wedgeprops=dict(width=0.5), startangle=-80, colors=colors)
    create_labels(wedges, curr_consumptions)
    ax.set_title("Current Consumption")
    plt.axis('equal')


    # Plot power consumption of each elment in a pie chart
    ax = plt.subplot(3, 2, 2)
    sensoring_power_consumption = sum([sensor.operating_voltage * sensor.get_total_energy() for sensor in system_consumption.get_sensoring_consumption()])
    microcontroller_power_consumption = microcontroller.operating_voltage * system_consumption.get_microcontroller_energy_consumption()
    radio_power_consumption = radio_interface.operating_voltage * system_consumption.get_communications_energy_consumption()
    sizes_pwr = [sensor.operating_voltage * sensor.get_total_energy() for sensor in system_consumption.get_sensoring_consumption()]
    sizes_pwr.extend([microcontroller_power_consumption, radio_power_consumption])
    # sizes = [sensoring_power_consumption, microcontroller_power_consumption, radio_power_consumption]
    total = sum(sizes_pwr)
    curr_consumptions = [sensor.name + "\n" + slices_values_pwr(sensor.get_total_energy() * sensor.operating_voltage) for sensor in system_consumption.get_sensoring_consumption()]
    curr_consumptions.extend([system_consumption.get_microcontroller_consumption().name + ":\n" + slices_values_pwr(microcontroller_power_consumption), system_consumption.get_communications_consumption().name + ":\n" + slices_values_pwr(radio_power_consumption)])
    # curr_consumptions = ["Sensors:\n" + slices_values_pwr(sensoring_power_consumption), system_consumption.get_microcontroller_consumption().name + ":\n" + slices_values_pwr(microcontroller_power_consumption), system_consumption.get_radio_interface_consumption().name + ":\n" + slices_values_pwr(radio_power_consumption)]
    wedges, texts = plt.pie(sizes_pwr, wedgeprops=dict(width=0.5), startangle=-80, colors=colors)
    create_labels(wedges, curr_consumptions)
    ax.set_title("Power Consumption")
    plt.axis('equal')

    ax = plt.subplot(3, 1, 2)
    # Plot a time series of the current consumption splitting between sensoring, communication and microcontroller consumptions
    plt.title("Current Consumption Time Series")

    # Plot microcontroller current consumption over the time
    timeseries = {}
    microcontroller_timeserie = [microcontroller.deep_sleep_consumption] * len(system_consumption.get_microcontroller_consumption().schedule)
    for i in range(len(system_consumption.get_microcontroller_consumption().schedule)):
        if system_consumption.get_microcontroller_consumption().schedule[i]:
            microcontroller_timeserie[i] = microcontroller.active_consumption
    timeseries[system_consumption.get_microcontroller_consumption().name] = microcontroller_timeserie

    # Plot radio current consumption over the time
    radio_timeserie = [radio_interface.inactive_consumption] * len(system_consumption.get_communications_consumption().schedule)
    for i in range(len(system_consumption.get_communications_consumption().schedule)):
        if system_consumption.get_communications_consumption().schedule[i]:
            radio_timeserie[i] = radio_interface.transmit_consumption
    timeseries[system_consumption.get_communications_consumption().name] = radio_timeserie

    # Plot sensors current consumption over the time
    for s in range(len(sensors)):
        sensor_schedule = system_consumption.get_sensoring_consumption()[s].schedule
        sensor_timeserie = [sensors[s].inactive_consumption] * len(sensor_schedule)
        for i in range(len(sensor_schedule)):
            if sensor_schedule[i]:
                sensor_timeserie[i] = sensors[s].active_consumption
        timeseries[sensors[s].get_name()] = sensor_timeserie
    mc_line = timeseries[microcontroller.name]
    x_values = np.linspace(0, duration, len(mc_line))
    # plt.plot(x_values, mc_line, label=microcontroller.name, drawstyle='steps-post')
    plt.fill_between(x_values, mc_line, step='post', color=colors[-2], linewidth=0)
    labels = [microcontroller.name]
    radio_line = [x + y for x, y in zip(mc_line, radio_timeserie)]
    labels.append(radio_interface.name)
    # plt.plot(x_values, radio_line, label=radio_interface.name, drawstyle='steps-post')
    plt.fill_between(x_values, mc_line, radio_line, step='post', color=colors[-1], linewidth=0)
    last_line = radio_line
    for sensor in sensors:
        labels.append(sensor.get_name())
        sensor_line = [x + y for x, y in zip(last_line, timeseries[sensor.get_name()])]
        # plt.plot(x_values, sensor_line, label=sensor.get_name(), drawstyle='steps-post')
        plt.fill_between(x_values, last_line, sensor_line, step='post', color=colors[sensors.index(sensor)], linewidth=0)
        last_line = sensor_line
    plt.legend(labels, loc='upper left', bbox_to_anchor=(0, 0, 0.5, 1))
    plt.xlabel("Time (s)")
    plt.ylabel("Current (mA)")
    table_data = [[
        "%.2f mAh" % (sum(timeseries[sensor.get_name()])/3600),
        "%.2f mA" % max(timeseries[sensor.get_name()]),
        "%.2f mA" % (np.mean(timeseries[sensor.get_name()])),
        "%.2f mWh" % (sum(timeseries[sensor.get_name()])*sensor.operating_voltage/3600),
        "%.2f mW" % (max(timeseries[sensor.get_name()])*sensor.operating_voltage),
        "%.2f mW" % (np.mean(timeseries[sensor.get_name()])*sensor.operating_voltage)] for sensor in sensors]
    table_data.append([
        "%.2f mAh" % (sum(microcontroller_timeserie)/3600),
        "%.2f mA" % max(microcontroller_timeserie),
        "%.2f mA" % (np.mean(microcontroller_timeserie)),
        "%.2f mWh" % (sum(microcontroller_timeserie)*microcontroller.operating_voltage/3600),
        "%.2f mW" % (max(microcontroller_timeserie)*microcontroller.operating_voltage),
        "%.2f mW" % (np.mean(microcontroller_timeserie)*microcontroller.operating_voltage)])
    table_data.append([
        "%.2f mAh" % (sum(radio_timeserie)/3600),
        "%.2f mA" % max(radio_timeserie),
        "%.2f mA" % (np.mean(radio_timeserie)),
        "%.2f mWh" % (sum(radio_timeserie)*radio_interface.operating_voltage/3600),
        "%.2f mW" % (max(radio_timeserie)*radio_interface.operating_voltage),
        "%.2f mW" % (np.mean(radio_timeserie)*radio_interface.operating_voltage)])
    ax = plt.subplot(3, 1, 3)
    table = matplotlib.table.table(ax, table_data, loc='center', cellLoc='center', colLabels=['Current Consumption (mAh)', 'Maximum Current (mA)', 'Average Current (mA)','Power Consumption (mWh)', 'Maximum Power (mW)', 'Average Power (mW)'], rowLabels=[sensor.get_name() for sensor in sensors] + [microcontroller.name, radio_interface.name])
    table.set_fontsize(24)
    table.scale(1, 2)
    plt.axis('off')
    plt.show()

# Main program
# First ask to the user if wants to enter a new sensor, microcontroller or radio interface
get_user_input()
# Read from prompt the sensors, microcontroller and radio interface
sensors = read_sensors()
microcontroller = read_microcontroller()
radio_interface = read_radio_interface()
# Read from prompt the duration of the measurement
duration = int(input("Enter the duration of the measurement (seconds): "))
# Calculate the energy consumption of the system
system_consumption = get_system_energy_consumption(sensors, microcontroller, radio_interface, duration)
# Generate plots and tables with the energy consumption of the system
show_consumptions(system_consumption)
print(f"Total energy consumption: {system_consumption} mAs")
