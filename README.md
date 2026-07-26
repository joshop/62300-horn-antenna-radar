# 3D-Printed Bistatic Radar System

This project is a custom radar system built to measure distance. It uses a NanoVNA v2 and two 3D-printed antennas—one to transmit signals and one to receive them. 

By tracking how long it takes for a radio signal to bounce off an object and return, the system calculates exactly how far away the object is.

## Hardware

*   **Antennas:** We designed horn-shaped antennas and 3D-printed them in basic plastic (PLA). 
*   **Tuning:** To make them work with radio waves, we lined the insides with conductive tape and manually trimmed the wire feeds until they were tuned perfectly for 2.45 GHz.

## Software & Results

*   **Python App:** We wrote a custom Python interface to control the NanoVNA from a laptop over USB. 
*   **Live Display:** The software does the math to turn the raw frequency data into distance and shows the results live on a scrolling chart, filtering out background noise.
*   **Accuracy:** After adjusting for the physical length of the antennas (a 30cm offset), the radar measured distances very accurately.
