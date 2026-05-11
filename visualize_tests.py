import numpy as np
import matplotlib.pyplot as plt
import csv

# data = "test-results/exponential-test.csv"
data = "test-results/conical-test.csv"

m = []
r = []

with open(data, mode='r') as file:
    reader = csv.DictReader(file)

    for row in reader:
        m.append(float(row["measured_dist"]))
        r.append(float(row["real_dist"]))

m = np.array(m)
r = np.array(r)

# remove the DC error to reject measurement error
m = m - np.mean(m-r)

plt.figure(figsize=(8, 6))

plt.plot(r, m, label="Measured", color="blue")
plt.plot(r, r, label="Real", color="red", linestyle="--")

plt.xlabel("Real distance (m)")
plt.ylabel("Distance (m)")
plt.title("Measured vs. Real Distances")

plt.xlim(0.75, 3.25)
plt.ylim(0.75, 3.25)

plt.legend()
plt.grid(True, linestyle=':', alpha=0.6)
plt.show()
