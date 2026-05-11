import skrf
from imgui_bundle import imgui, immapp, implot
from skrf.vi.vna.nanovna import NanoVNAv2
import numpy as np
import os
import threading
import scipy
import time

s11 = skrf.Network()
s21 = skrf.Network()
s11a = None
s21a = None
freq = skrf.Frequency(start=2, stop=3, unit='GHz', npoints=41)
s11.frequency = freq
s21.frequency = freq
cal_short = None
cal_open = None
cal_load = None
cal_thru = None
calibration = None


def update_calibration():
    global calibration
    if cal_short is None or cal_open is None or cal_load is None or cal_thru is None:
        return
    cal_measured = [cal_short, cal_open, cal_load, cal_thru]
    line = skrf.DefinedGammaZ0(frequency=cal_measured[0].frequency, z0=50)
    cal_ideals = [line.short(nports=2), line.open(nports=2), line.match(nports=2), None]

    # run calibration
    calibration = skrf.calibration.calibration.SOLT(ideals=cal_ideals, measured=cal_measured)
    calibration.run()

serial_running = False
ser_port = '/dev/ttyACM0'
last_recv_time = 0
last_recv_delay = 0
need_upd_freq = False
distances_mode = True

mono_font = None
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)
def load_fonts():
    io = imgui.get_io()

    path = resource_path("LiberationMono-Regular.ttf")
    print(path)

    # Adjust path as needed for your system
    mono_font = io.fonts.add_font_from_file_ttf(
        path,
        40.0,
    )

    return mono_font

def serial_reader():
    global s11, s21, s11a, s21a, freq, last_recv_time, last_recv_delay, need_upd_freq
    # recv_times = []
    last_recv_time = 0
    last_recv_delay = 0
    vna = NanoVNAv2(f"ASRL{ser_port}::INSTR")
    vna.frequency = freq
    while serial_running:
        if need_upd_freq:
            need_upd_freq = False
            vna.frequency = freq
        s11a, s21a = vna.get_s11_s21()
        snet = skrf.network.four_oneports_2_twoport(s11a, s21a, s21a, s11a)
        if calibration is not None:
            snet = calibration.apply_cal(snet)
        s11 = s11a.copy()
        s11.s[:, 0, 0] = snet.s[:, 0, 0]
        s21 = s21a.copy()
        s21.s[:, 0, 0] = snet.s[:, 1, 0]
        # recv_times.append(time.time())
        last_recv_delay = time.time() - last_recv_time
        last_recv_time = time.time()
    s11 = skrf.Network()
    s21 = skrf.Network()
    s11a = None
    s21a = None
y_bkg = None
history = np.zeros((600, 200))
lower_freq = 2
upper_freq = 3
heatmap_max = 1
num_sweep_pts = 41
max_t_time = 20
ns_to_m = 0.299792458 / 2
sensi = 5
def gui():
    global cal_short, cal_open, cal_load, cal_thru, calibration, y_bkg, history, heatmap_max, ser_port, serial_running, lower_freq, upper_freq, num_sweep_pts, freq, need_upd_freq, max_t_time, distances_mode, sensi, mono_font
    imgui.begin("VNA Interface")
    _, ser_port = imgui.input_text("Port number", ser_port)

    if serial_running:
        imgui.push_style_color(imgui.Col_.button, (1.0, 0.0, 0.0, 0.4))
    else:
        imgui.push_style_color(imgui.Col_.button, (0.0, 1.0, 0.0, 0.4))
    if imgui.button("Connect" if not serial_running else "Disconnect"):
        if serial_running:
            serial_running = False
        else:
            serial_running = True
            threading.Thread(target=serial_reader, daemon=True).start()
    imgui.pop_style_color()
    if serial_running:
        if last_recv_time < time.time()-3:
            imgui.text("Receiving: ?")
        else:
            imgui.text(f"Receiving: {1/last_recv_delay:.2f}/s")
    else:
        imgui.text("Disconnected")

    imgui.text("Sweep Setup")
    _, lower_freq = imgui.input_float("Start (GHz)", lower_freq)
    _, upper_freq = imgui.input_float("Stop (GHz)", upper_freq)
    _, num_sweep_pts = imgui.input_int("Points", num_sweep_pts)
    if imgui.button("Update Sweep"):
        freq = skrf.Frequency(start=lower_freq, stop=upper_freq, unit='GHz', npoints=num_sweep_pts)
        need_upd_freq = True


    imgui.end()
    imgui.begin("Data view")
    if implot.begin_plot("S-parameters"):

        implot.setup_axis_format(implot.ImAxis_.y1, "%g dB")
        implot.setup_axis_limits(implot.ImAxis_.y1, -100, 10, imgui.Cond_.always)
        implot.setup_axis_limits(implot.ImAxis_.x1, min(freq.f), max(freq.f), imgui.Cond_.always)
        if s11.nports == 1:
            mag = np.abs(s11.s[:, 0, 0])
            logmag = 20 * np.log10(mag)
            if not np.any(np.isnan(logmag)):
                implot.plot_line("S11", freq.f, logmag)
        if s21.nports == 1:
            mag = np.abs(s21.s[:, 0, 0])
            logmag = 20 * np.log10(mag)
            if not np.any(np.isnan(logmag)):
                implot.plot_line("S21", freq.f, logmag)
        implot.end_plot()
    imgui.end()
    imgui.begin("FFT")
    last_y = None
    max_val = 1
    do_rescale = False
    targets = []
    if imgui.button("Rescale"):
        do_rescale = True
    if implot.begin_plot("Impulse Response"):
        implot.setup_axis_format(implot.ImAxis_.x1, "%g m" if distances_mode else "%g ns")
        implot.setup_axis_limits(implot.ImAxis_.x1, 0, max_t_time, imgui.Cond_.always)
        if s21.nports == 1:
            # s21_ext = s21.extrapolate_to_dc()
            s21_ext = s21
            t, y = s21_ext.impulse_response(window='hann', pad=1024)
            y = np.abs(y)
            last_y = y.copy()
            if y_bkg is not None:
                y -= y_bkg
            t *= 1e9
            if distances_mode:
                t *= ns_to_m
            targets, prom = scipy.signal.find_peaks(y, prominence=(max(y)/sensi, None), distance=30)
            # print(targets)
            targets = t[targets]
            prom = prom['prominences']
            targets = targets[np.argsort(-prom)]
            max_t_time = max(t)
            max_val = np.max(y)
            if do_rescale:
                implot.setup_axis_limits(implot.ImAxis_.y1, 0, 1.2*max_val, imgui.Cond_.always)
                heatmap_max = max_val

            implot.plot_line("S21", t, y)
            old = len(t[t >= 0])
            new_indices = np.linspace(0, old - 1, 200)
            new_y = np.interp(new_indices, np.arange(old), y[t >= 0])
            history = np.roll(history, 1, axis=0)
            history[0, :] = new_y
        implot.end_plot()
    if imgui.button("Capture Background") and last_y is not None:
        y_bkg = last_y

    imgui.end()

    imgui.begin("Targets")

    if mono_font is None:
        mono_font = load_fonts()

    _, sensi= imgui.input_int("Sensitivity", sensi)
    imgui.push_font(mono_font, 40.0)
    for t in targets:
        imgui.text_unformatted(f"{t:.3f} m")
    imgui.pop_font()
    imgui.end()


    imgui.begin("Waterfall")
    if implot.begin_plot("Distance Waterfall", flags=implot.Flags_.no_legend.value | implot.Flags_.no_mouse_text.value, size=(-1, -1)):

        implot.setup_axis(implot.ImAxis_.x1, "Distance (m)" if distances_mode else "Time (ns)")
        implot.setup_axis(implot.ImAxis_.y1, "History")
        implot.setup_axis_limits(implot.ImAxis_.x1, 0, max_t_time, imgui.Cond_.always)
        implot.setup_axis_limits(implot.ImAxis_.y1, 0, 600, imgui.Cond_.always)
        implot.push_colormap(implot.Colormap_.plasma)
        implot.plot_heatmap("heat", history, scale_min=0, scale_max = heatmap_max, label_fmt="", bounds_min = implot.Point(0, 600), bounds_max = implot.Point(max_t_time, 0))
        implot.pop_colormap()
        implot.end_plot()
    imgui.end()
    if s11a is not None and s21a is not None:
        snet = skrf.network.four_oneports_2_twoport(s11a, s21a, s21a, s11a)
    else:
        snet = None


    imgui.begin("Calibration")

    if imgui.button("Save Calibration"):
        if cal_short is not None: cal_short.write("short.ntwk")
        if cal_open is not None: cal_open.write("open.ntwk")
        if cal_load is not None: cal_load.write("load.ntwk")
        if cal_thru is not None: cal_thru.write("thru.ntwk")
    if imgui.button("Load Calibration"):
        if os.path.isfile("short.ntwk"):
            cal_short = skrf.network.Network()
            cal_short.read("short.ntwk")

        if os.path.isfile("open.ntwk"):
            cal_open = skrf.network.Network()
            cal_open.read("open.ntwk")

        if os.path.isfile("load.ntwk"):
            cal_load = skrf.network.Network()
            cal_load.read("load.ntwk")

        if os.path.isfile("thru.ntwk"):
            cal_thru = skrf.network.Network()
            cal_thru.read("thru.ntwk")
    if imgui.button("Clear Calibration"):
        cal_short = None
        cal_open = None
        cal_load = None
        cal_thru = None
        calibration = None

    if cal_short is None:
        imgui.push_style_color(imgui.Col_.button, (1.0, 0.0, 0.0, 0.4))
    else:
        imgui.push_style_color(imgui.Col_.button, (0.0, 1.0, 0.0, 0.4))
    if imgui.button("Short"):
        cal_short = snet
    imgui.pop_style_color()


    if cal_open is None:
        imgui.push_style_color(imgui.Col_.button, (1.0, 0.0, 0.0, 0.4))
    else:
        imgui.push_style_color(imgui.Col_.button, (0.0, 1.0, 0.0, 0.4))
    if imgui.button("Open"):
        cal_open = snet
    imgui.pop_style_color()


    if cal_load is None:
        imgui.push_style_color(imgui.Col_.button, (1.0, 0.0, 0.0, 0.4))
    else:
        imgui.push_style_color(imgui.Col_.button, (0.0, 1.0, 0.0, 0.4))
    if imgui.button("Load"):
        cal_load = snet
    imgui.pop_style_color()

    if cal_thru is None:
        imgui.push_style_color(imgui.Col_.button, (1.0, 0.0, 0.0, 0.4))
    else:
        imgui.push_style_color(imgui.Col_.button, (0.0, 1.0, 0.0, 0.4))
    if imgui.button("Thru"):
        cal_thru = snet
    imgui.pop_style_color()


    if cal_short is None or cal_open is None or cal_load is None or cal_thru is None:
        imgui.begin_disabled()
    if imgui.button("Update Calibration"):
        update_calibration()
    if cal_short is None or cal_open is None or cal_load is None or cal_thru is None:
        imgui.end_disabled()

    _, distances_mode = imgui.checkbox("Display Distances", distances_mode)

    imgui.end()




imgui.create_context()
implot.create_context()
imgui.get_io().set_ini_filename("radar_gui.ini")

runner_params = immapp.RunnerParams()
runner_params.fps_idling.enable_idling = False

immapp.run(
    gui_function=gui,
    window_title="Radar GUI",
    window_size=(900, 600),
    window_restore_previous_geometry=True,
    fps_idle = 60
    #on_exit=on_exit,
)
