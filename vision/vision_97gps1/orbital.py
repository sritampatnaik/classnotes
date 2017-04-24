import datetime
import numpy as np

F = 1 / 298.257223563 # Dunya duzlestirme WGS-84
MFACTOR = 7.292115E-5 
EPS_COS = 1.5e-12
F = 1 / 298.257223563  # Dunya duzlestirme WGS-84
A = 6378.137  # WGS84 ekvotarsal cap

def jdays2000(utc_time):
    """2000'den itibaren gecen gunler
    """
    return _days(utc_time - datetime(2000, 1, 1, 12, 0))
    

def jdays(utc_time):
    """UTC zamaninini julyen zamanina degistir
    """
    return jdays2000(utc_time) + 2451545

def _fdays(dt):
    """d_t'den reel sayi bazinda gunleri al
    """
    return (dt.days +
            (dt.seconds +
             dt.microseconds / (1000000.0)) / (24 * 3600.0))

_vdays = np.vectorize(_fdays)

def _days(dt):
    """Get the days (floating point) from *d_t*.
    """
    try:
        return _fdays(dt)
    except AttributeError:
        return _vdays(dt)

def gmst(utc_time):
    """Greenwich mean sidereal utc_time, in radians.    
    As defined in the AIAA 2006 implementation:
    http://www.celestrak.com/publications/AIAA/2006-6753/
    """
    ut1 = jdays2000(utc_time) / 36525.0
    theta = 67310.54841 + ut1 * (876600 * 3600 + 8640184.812866 + ut1 *
                                 (0.093104 - ut1 * 6.2 * 10e-6))
    return np.deg2rad(theta / 240.0) % (2 * np.pi)
    

def observer_position(time, lon, lat, alt):
    """Calculate observer ECI position.
    http://celestrak.com/columns/v02n03/
    """
    
    lon = np.deg2rad(lon)
    lat = np.deg2rad(lat)
    
    theta = (gmst(time) + lon) % (2 * np.pi)
    c = 1 / np.sqrt(1 + F * (F - 2) * np.sin(lat)**2)
    sq = c * (1 - F)**2

    achcp = (A * c + alt) * np.cos(lat)
    x = achcp * np.cos(theta)  # kilometers
    y = achcp * np.sin(theta)
    z = (A * sq + alt) * np.sin(lat)

    vx = -MFACTOR*y  # kilometers/second
    vy = MFACTOR*x
    vz = 0
    return (x, y, z), (vx, vy, vz)   

def get_observer_look(sat_lon, sat_lat, sat_alt, utc_time, lon, lat, alt):
    """Calculate observers look angle to a satellite.
    http://celestrak.com/columns/v02n02/
    utc_time: Observation time (datetime object)
    lon: Longitude of observer position on ground
    lat: Latitude of observer position on ground
    alt: Altitude above sea-level (geoid) of observer position on ground
    Return: (Azimuth, Elevation)
    """
    (pos_x, pos_y, pos_z), (vel_x, vel_y, vel_z) = \
        observer_position(utc_time, sat_lon, sat_lat, sat_alt)

    (opos_x, opos_y, opos_z), (ovel_x, ovel_y, ovel_z) = \
        observer_position(utc_time, lon, lat, alt)

    lon = np.deg2rad(lon)
    lat = np.deg2rad(lat)

    theta = (gmst(utc_time) + lon) % (2 * np.pi)

    rx = pos_x - opos_x
    ry = pos_y - opos_y
    rz = pos_z - opos_z

    sin_lat = np.sin(lat)
    cos_lat = np.cos(lat)
    sin_theta = np.sin(theta)
    cos_theta = np.cos(theta)

    top_s = sin_lat * cos_theta * rx + \
        sin_lat * sin_theta * ry - cos_lat * rz
    top_e = -sin_theta * rx + cos_theta * ry
    top_z = cos_lat * cos_theta * rx + \
        cos_lat * sin_theta * ry + sin_lat * rz

    az_ = np.arctan(-top_e / top_s)

    az_ = np.where(top_s > 0, az_ + np.pi, az_)
    az_ = np.where(az_ < 0, az_ + 2 * np.pi, az_)

    rg_ = np.sqrt(rx * rx + ry * ry + rz * rz)
    el_ = np.arcsin(top_z / rg_)

    return np.rad2deg(az_), np.rad2deg(el_)
