#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""

Based on https://pypi.org/project/swinging-door/ of "Aleksandr F. Mikhaylov (ChelAxe)
Replaced the nomenclature with the one used by GE Proficy Historian in flwg. presentation https://slideplayer.com/slide/3884/ (https://softwaredocs.weatherford.com/cygnet/94/Content/Topics/History/CygNet%20Swinging%20Door%20Compression.htm)
Added deadband compression.
Added timeout.
Added slightly modified point generator which accepts a timestamp as type string as well as datetime.
Always archive the last point.

"""

__author__ = "Peter Vanhevel (td03pvh)"
__version__ = "v3.0"
__date__ = "2022-04-20"

import pandas as pd
import numpy as np
from datetime import datetime


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __call__(self):
        return self.x, self.y


def point_generator(data):
    """
    Generate a point.

    Parameters
    ----------
    data : list of tuple (float, float)
        Typically 2 dataframe columns (timestamp & value).

    Yields
    ------
    tuple (float, float)
        A tuple with a timestamp converted to timestamp() and a float value.
    """
    date_format = "%Y-%m-%d %H:%M:%S"
    for date_, value in data.values.tolist():
        if isinstance(date_, datetime):
            # yield date_.timestamp(), value
            # !!!!!!
            yield datetime.strptime(str(date_), date_format).timestamp(), value
        else:
            yield datetime.strptime(date_, date_format).timestamp(), value


def dead_band_compression(generator, deviation=0.1, timeout=0):
    """
    Reduce size of historian log using the dead band compression algorithm.

    Parameters
    ----------
    generator : tuple (float, float)
        It works by examining data and discarding any that does not exceed a defined limit
        (e.g. +/- 0.5 Deg F.).
    deviation : float
        The deviation is the dead band width divided by 2. The default is 0.1.
    timeout : integer
        If a value is held for a period of time that exceeds the timeout period, the next data point
        is considered to exceed the deadband value, regardless of the actual data received.
        The default is 0 seconds, which actually means "no timeout".

    Yields
    ------
    new_point : Point
        A new point.
    archived_point : Point
        An “Archived Point” is one that is stored.
        After a point is archived, the next point becomes the held point.
    previous_point : Point
        Previous new_point.

    """
    if timeout == 0:
        timeout = np.inf
    archived_point = previous_point = new_point = Point(*(next(generator)))
    archived_point_up = Point(archived_point.x, archived_point.y + deviation)
    archived_point_down = Point(archived_point.x, archived_point.y - deviation)

    # The first point is always archived
    yield archived_point()

    while True:
        try:
            previous_point = new_point
            # Go to next point
            new_point = Point(*(next(generator)))
        except StopIteration:                                                                       # Last point has been reached
            yield new_point()
            break

        ellapsed_time_since_last_archived_point = (new_point.x - archived_point.x)

        if (
            (ellapsed_time_since_last_archived_point >= timeout) |
            ((new_point.y > archived_point_up.y) | (new_point.y < archived_point_down.y))
        ):
            if previous_point() != archived_point():
                yield previous_point()
            # New point complies and therefore is archived
            archived_point = new_point
            archived_point_up = Point(archived_point.x, archived_point.y + deviation)
            archived_point_down = Point(archived_point.x, archived_point.y - deviation)
            yield archived_point()


def swinging_door_compression(generator, deviation=0.1, timeout=0):
    """
    Reduce size of historian log using the swinging door compression algorithm.

    Parameters
    ----------
    generator : tuple(float,float)
        It works by examining data and discarding any that falls within a slope range.
    deviation : float
        The deviation is the dead band width divided by 2. The default is 0.1.
    timeout : integer
        If a value is held for a period of time that exceeds the timeout period, the next data point
        is considered to exceed the deadband value, regardless of the actual data received or the
        calculated slope.
        The default is 0 seconds, which actually means "no timeout".

    Yields
    ------
    new_point : Point
        A new point.
    archived_point : Point
        An “Archived Point” is one that is stored.
        After a point is archived, the next point becomes the held point.
    held_point : Point
        A “Held Point” is the last good value that arrived. We don’t know if it will be stored until
        the next value arrives to tell us if the slope has changed sufficiently.

    """
    if timeout == 0:
        timeout = np.inf
    archived_point = held_point = new_point = Point(*(next(generator)))
    held_point_up = Point(held_point.x, held_point.y + deviation)
    held_point_down = Point(held_point.x, held_point.y - deviation)
    lowest_upper_slope = highest_lower_slope = 0.0

    # The first point is always archived
    yield archived_point()

    while True:
        try:
            # Go to next point
            new_point = Point(*(next(generator)))
            # print({datetime.fromtimestamp(new_point.x)})
        except StopIteration:                                                                       # Last point has been reached
            yield new_point()
            break

        upper_slope = (new_point.y - held_point_up.y) / (new_point.x - held_point_up.x)
        lower_slope = (new_point.y - held_point_down.y) / (new_point.x - held_point_down.x)

        if not lowest_upper_slope and not highest_lower_slope:
            lowest_upper_slope = upper_slope
            highest_lower_slope = lower_slope
            continue

        # timeout = 0 actually means no timeout
        ellapsed_time_since_last_archived_point = (new_point.x - archived_point.x)
        if ellapsed_time_since_last_archived_point >= timeout:
            # The held point is archived
            archived_point = held_point = new_point
            yield archived_point()

            held_point_up = Point(held_point.x, held_point.y + deviation)
            held_point_down = Point(held_point.x, held_point.y - deviation)
            lowest_upper_slope = highest_lower_slope = 0.0

            continue

        # If the slope of the line N, connecting the archived point with the new point,
        # is between the upper and lower slopes, it intersects the dead band of the held point.
        elif (upper_slope > lowest_upper_slope):
            # With each new point the process is continued,
            # narrowing the aperture and discarding unnecessary points as you go.
            lowest_upper_slope = upper_slope
            if lowest_upper_slope > highest_lower_slope:
                slope = (new_point.y - archived_point.y) / (new_point.x - archived_point.x)
                calc_held_point_x = (
                    (
                        held_point_up.y - archived_point.y +
                        slope * archived_point.x - highest_lower_slope * held_point.x
                    )
                ) / (slope - highest_lower_slope)
                calc_held_point_y = held_point_up.y - deviation / 2 + (
                    highest_lower_slope * (calc_held_point_x - held_point.x)
                )
                held_point = Point(calc_held_point_x, calc_held_point_y)

                # The held point is archived
                archived_point = held_point
                yield archived_point()

                held_point_up = Point(held_point.x, held_point.y + deviation)
                held_point_down = Point(held_point.x, held_point.y - deviation)

                # Calculate the slopes of the two lines, U and L, connecting the archived point
                # with the upper and lower ends of the error bands (dead band) associated with the held point.
                lowest_upper_slope = upper_slope = (new_point.y - held_point_up.y) / (
                    new_point.x - held_point_up.x
                )
                highest_lower_slope = lower_slope = (new_point.y - held_point_down.y) / (
                    new_point.x - held_point_down.x
                )

        elif (lower_slope < highest_lower_slope):
            # With each new point the process is continued,
            # narrowing the aperture and discarding unnecessary points as you go.
            highest_lower_slope = lower_slope
            if lowest_upper_slope > highest_lower_slope:
                slope = (new_point.y - archived_point.y) / (new_point.x - archived_point.x)
                calc_held_point_x = (
                    (
                        held_point_down.y - archived_point.y +
                        slope * archived_point.x - lowest_upper_slope * held_point_down.x
                    )
                ) / (slope - lowest_upper_slope)
                calc_held_point_y = held_point_down.y + deviation / 2 + (
                    lowest_upper_slope * (calc_held_point_x - held_point_down.x)
                )
                held_point = Point(calc_held_point_x, calc_held_point_y)

                # The held point is archived
                archived_point = held_point
                yield archived_point()

                held_point_up = Point(held_point.x, held_point.y + deviation)
                held_point_down = Point(held_point.x, held_point.y - deviation)

                # Calculate the slopes of the two lines, U and L, connecting the archived point
                # with the upper and lower ends of the error bands (dead band) associated with the held point.
                lowest_upper_slope = upper_slope = (new_point.y - held_point_up.y) / (
                    new_point.x - held_point_up.x
                )
                highest_lower_slope = lower_slope = (new_point.y - held_point_down.y) / (
                    new_point.x - held_point_down.x
                )

        # If the slope of the new point is within the critical aperture window, the previous held point may be discarded.
        # You can forget about this point now.
        else:
            # The start of the while loop creates a new held point
            continue


def main():
    global df
    print("The results of flwg. 3 input formats should be identical:")
    timestamp_format = "%Y-%m-%d %H:%M:%S"
    df = pd.DataFrame()
    df["ts"] = ["2018-05-27 06:15:39"]
    df["value"] = 1
    point = point_generator(df)
    print(next(point))
    df["ts"] = df.apply(lambda row: pd.to_datetime(row["ts"], format=timestamp_format), axis=1)
    point = point_generator(df)
    print(next(point))
    df["ts"] = df.apply(lambda row: str(row["ts"]), axis=1)
    point = point_generator(df)
    print(next(point))


if __name__ == "__main__":
    main()
