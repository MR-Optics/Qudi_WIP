import os.path

import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit

sns.set_theme(style='whitegrid')


def plot_pulse():
    data = np.loadtxt('C:\Data\\2022\\06\\20220607\\PulsedMeasurement\\20220607-1542-53_raw_timetrace.dat')

    col1_data = data[:, 1]
    col2_data = data[:, -1]
    xdata = np.arange(1, len(col1_data) + 1)

    # popt, pcov = curve_fit(func, xdata, ydata, maxfev=10000)
    #
    # print(f"Fit params: {popt}")
    plt.plot(xdata / 20, col1_data, '-', label='Second pulse', markersize=2, color='b')
    plt.plot(xdata / 20, col2_data, '-', label='Last pulse', markersize=2, color='r')
    # plt.plot(xdata, func(xdata, *popt), label='Fitted curve')

    plt.xlabel(r"$t ~ (\mathrm{\mu} \mathrm{s})$")
    plt.ylabel('counts []')
    #plt.title('G300-IR100-mW')
    plt.ylim([-2, 850])
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join("Analysis", "T1", "Pulse.pdf"), bbox_inches="tight", pad_inches=0.03)
    plt.show()


def double_exp(x, a, b, c):
    #return a + b * np.exp(-x / c) + d * np.exp(-x / e)
    return a + b * np.exp(-(x / c) ** 0.89)



def plot_T1():
    data = np.loadtxt('C:\Data\\2022\\06\\20220607\\PulsedMeasurement\\20220607-1542-53_pulsed_measurement.dat')
    xdata, ydata = data[25:, 0], data[25:, 1]

    #popt, pcov = curve_fit(double_exp, xdata, ydata, bounds=((-np.inf, -np.inf, 0, -np.inf, 0), (np.inf, np.inf, np.inf, np.inf, np.inf)), maxfev=10000)
    popt, pcov = curve_fit(double_exp, xdata, ydata, bounds=((-np.inf, -np.inf, 0), (np.inf, np.inf, np.inf)), maxfev=10000)
    print(f"Fit params: {popt * 1e6}")
    print(f"Cov params: {pcov * 1e12}")

    plt.plot(xdata * 1000000, ydata, 'o', label='data', markersize=2, color=(0, 0, 1))
    plt.plot(xdata * 1000000, double_exp(xdata, *popt), label='Fitted curve', color='r')

    plt.xlabel(r"$t ~ (\mathrm{\mu} \mathrm{s})$")
    plt.ylabel('counts []')
    #plt.title('G300-IR100-mW')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join("Analysis", "T1", "T1.pdf"), bbox_inches="tight", pad_inches=0.03)
    plt.show()


if __name__ == '__main__':
    plot_T1()
    #plot_pulse()
