import math
from panda3d.core import Point3

def cube2hex(h):
    x=h[0]
    y=h[1]
    z=h[2]
    col = x + (z + (z%2)) / 2.0
    row = z    
    return (int(row), int(col))
    
def hex2cube(h):
    row=h[0]
    col=h[1]
    x = col - (row + (row%2)) / 2.0
    z = row
    y = -x-z    
    return [x, y, z]

def cubeRound(h):
    rx = round(h[0])
    ry = round(h[1])
    rz = round(h[2])
    x_diff = abs(rx - h[0])
    y_diff = abs(ry - h[1])
    z_diff = abs(rz - h[2])
    if x_diff > y_diff and x_diff > z_diff:
        rx = -ry-rz
    elif y_diff > z_diff:
        ry = -rx-rz
    else:
        rz = -rx-ry
    return [rx, ry, rz]

def hexRound(h):
    return cube2hex(cubeRound(hex2cube(h)))

def point2Hex(p, size=12.0):
    x=p[0]
    y=p[1]
    q = x * 2.0/3.0 / size
    r =(-x / 3.0 + math.sqrt(3.0)/3.0 * y) / size
    return hexRound([q, r])

def hex2Point(hexagon, size=12.0):
    x = size * 3.0/2.0 * hexagon[0]
    y = size * math.sqrt(3.0) * (hexagon[1] + hexagon[0]/2.0)
    return Point3(x, y, 0)
