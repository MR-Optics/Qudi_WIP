import os.path

import numpy as np
import seaborn as sns
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit



# import matplotlib
# import numpy as np
# import matplotlib.pyplot as plt
import numpy.fft
# import scipy.io
# from scipy.optimize import curve_fit
# import seaborn as sns

# matplotlib.rcParams['text.usetex'] = True

sns.set_theme(style="whitegrid", palette="muted")

# define the true objective function
def objective(x, a, b, c):
    return a / (b + c * x ** 2)


if __name__ == '__main__':
    #plt.scatter(range(1000), np.random.randn(1000))
    #plt.show()

    # dt = 20e-3
    # fps = 1 / dt
    # N = 1000
    kB = 1.38e-23  # Boltzmann constant [m^2kg/s^2K]
    T = 273.15 + 25  # Temperature [K]
    r = (2.8 / 2) * 1e-6  # Particle radius [m]
    v = 0.00002414 * 10 ** (247.8 / (-140 + T))  # Water viscosity [Pa*s]
    gamma = np.pi * 6 * r * v  # [m*Pa*s]

    #dataf = np.loadtxt('PSD-TrappedNDs/3-6-22/3-6-Trapped-StrongTrap.FD.dat')
    #f, x_f, y_f, z_f = dataf[:, 0], dataf[:, 1], dataf[:, 2], dataf[:, 3]

    #plt.figure()
    #plt.plot(f, x_f)
    #plt.xlabel('f [Hz]')
    #plt.ylabel('PSD [micro m]')
    #plt.show()


    data = np.loadtxt('M:\Experimental\\QPD(TrappingData)\\06.09.22\\06-09-22-Agg in cell.TD.dat')
    t, x_t, y_t, z_t = data[:, 0], data[:, 1], data[:, 2], data[:, 3]

    N = len(t)

    plt.figure()
    plt.plot(t, x_t, color='red')
    plt.xlabel('t [s]')
    plt.ylabel('x')
    #plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join("Analysis", "T1", "x.pdf"), bbox_inches="tight", pad_inches=0.03)
    plt.show()

    plt.figure()
    plt.plot(t, y_t, color='blue')
    plt.xlabel('t [s]')
    plt.ylabel('y')
    #plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join("Analysis", "T1", "y.pdf"), bbox_inches="tight", pad_inches=0.03)

    plt.show()

    plt.figure()
    plt.plot(t, z_t, color='green')
    plt.xlabel('t [s]')
    plt.ylabel('z')
    #plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join("Analysis", "T1", "z.pdf"), bbox_inches="tight", pad_inches=0.03)

    plt.show()




    plt.figure()
    plt.plot(x_t, y_t, color='black')
    plt.xlabel('x')
    plt.ylabel('y')
    #plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join("Analysis", "T1", "trajectory.pdf"), bbox_inches="tight", pad_inches=0.03)

    plt.show()



    freqs = 1 / (t[2] - t[1])
    freq = np.arange(0, freqs / 2 + freqs / N, freqs / N)

    xdft = numpy.fft.fft(x_t.flatten())
    # xdft = xdft(1:N / 2 + 1)
    xdft = xdft[0:N // 2 + 1]
    psdx = (1 / (freqs * N)) * np.abs(xdft) ** 2
    psdx[1:-1] = 2 * psdx[1:-1]


    plt.figure()
    plt.loglog(freq, psdx, label="PSD data", markersize=1)
    # plt.ylim([1e-7, 1e2])
    plt.xlabel('Frequency (Hz)')
    plt.ylabel(r"PSD ($\mathrm{\mu} \mathrm{m}^2$/Hz)")
    #plt.ylim([1e-8, 1])

    popt, _ = curve_fit(objective, freq, psdx)
    # summarize the parameter values
    a, b, c = popt
    print(f"y = {a} / ({b} + {c} * x^2)")
    # plot input vs output
    # define a sequence of inputs between the smallest and largest known inputs
    t_line = np.linspace(min(freq), max(freq), 10000)
    # calculate the output for the range
    x_line = objective(t_line, a, b, c)
    # create a line plot for the mapping function
    plt.loglog(t_line, x_line, '-', label="Fitted Lorentzian", color='red')

    plt.legend()
    plt.tight_layout()
    plt.savefig("psd.pdf", bbox_inches="tight", pad_inches=0.03)
    plt.show()

def PSD_L(x, d):
    return 0.0002 / (500 + d * x ** 2)

def plot_PSD():
    popt, pcov = curve_fit(PSD_L, freq, psdx, maxfev=10000)
    print(f"Fit params: {popt}")

    plt.loglog(freq, psdx, label='data', markersize=2)
    plt.plot(freq, PSD_L(freq, *popt), label='Fitted curve', color='red')
    plt.legend()
    plt.tight_layout()
    plt.savefig("psd.pdf", bbox_inches="tight", pad_inches=0.03)
    plt.show()

if __name__ == '__main__':
    # plot_pulse()
    plot_PSD()



