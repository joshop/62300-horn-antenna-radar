import numpy as np
from scipy.optimize import fsolve
from numpy import sqrt, pi, asin, tan
wgd = 2.54*2.5
G0d = 12.9
G0 = 10**(G0d/10)
a = 2.54*3.0 # 3.0 in
b = 2.54*3.0 # 1.7 in
#G0 = 10**(2.26)#10**(1.2)
lamb = 3e8 / (2.45e9) * 100
xrel = lambda x: (2*x-1)*(sqrt(2*x) - b / lamb)**2 - (sqrt(3/(2*pi))*(G0/(2*pi))*(1/sqrt(x))-a/lamb)**2*(G0**2/(6*pi**3)*(1/x)-1)
root = fsolve(xrel, G0/(2*pi*sqrt(2*pi)))[0]
pe = root * lamb
ph = G0**2 / (8 * pi**3) * (1 / root) * lamb
p = ph

# a1 = sqrt(3 * lamb * ph)
# b1 = sqrt(2 * lamb * pe)
d1 = sqrt(3 * lamb * p)
#
# theta1 = asin((b1/2) / pe)
# cut1 = (b/2) / tan(theta1)
# dist1 = sqrt(pe**2 - (b1/2)**2) - cut1

theta2 = asin((d1/2) / p)
cut2 = (a/2) / tan(theta2)
dist2 = sqrt(p**2 - (d1/2)**2) - cut2
dist1 = dist2
#print(dist1, dist2)
print(f"gain = {10*np.log10(G0)} dB")
print(f"waveguide: {a/2.54:.3f} in diameter")
print(f"aperture: {d1/2.54:.3f} in diameter")
print(f"horn length: {dist1/2.54:.3f} in")
