#! /usr/bin/env python
#
# tests.py

# system imports
import datetime
#
from hcron.library import date_to_bitmasks, list_st_to_bitmask, WHEN_BITMASKS, WHEN_MIN_MAX, WHEN_NAMES

list_st_to_bitmaskTests = [
    # dow
    (("0", "when_dow"), "0b1"),
    (("1", "when_dow"), "0b10"),
    (("2", "when_dow"), "0b100"),
    (("3", "when_dow"), "0b1000"),
    (("4", "when_dow"), "0b10000"),
    (("5", "when_dow"), "0b100000"),
    (("6", "when_dow"), "0b1000000"),
    #
    (("2009", "when_year"), "0b1000000000"),
    (("*/2", "when_month"), "0b10101010101"),
    (("1-4", "when_month"), "0b1111"),
    (("1-4/2", "when_month"), "0b101"),
    (("5-12/2", "when_month"), "0b10101010000"),
    (("*/2", "when_hour"), "0b10101010101010101010101"),
    (("0-23/2", "when_hour"), "0b10101010101010101010101"),
    (("0-23/3", "when_hour"), "0b1001001001001001001001"),
    (("0-2/2,4-5", "when_hour"), "0b110101"),
    # saw problem between 2009-11-07T00:00:01 and <2009-11-09T00:00:01
    (("2009", "when_year"), "0b1000000000"),
    (("11", "when_month"), "0b10000000000"),
    (("07", "when_day"), "0b1000000"),
    (("00", "when_hour"), "0b1"),
    (("00", "when_minute"), "0b1"),

    (("*", "when_year"),    "0b111111111111111111111111111111111111111111111111111"),
    (("2000", "when_year"), "0b1"),
    (("2050", "when_year"), "0b100000000000000000000000000000000000000000000000000"),
    (("*", "when_month"),   "0b111111111111"),
    (("1", "when_month"),   "0b1"),
    (("12", "when_month"),  "0b100000000000"),
    (("*", "when_day"),     "0b1111111111111111111111111111111"),
    (("1", "when_day"),     "0b1"),
    (("31", "when_day"),    "0b1000000000000000000000000000000"),
    (("*", "when_hour"),    "0b111111111111111111111111"),
    (("0", "when_hour"),    "0b1"),
    (("23", "when_hour"),   "0b100000000000000000000000"),
    (("*", "when_minute"),  "0b111111111111111111111111111111111111111111111111111111111111"),
    (("0", "when_minute"),  "0b1"),
    (("59", "when_minute"), "0b100000000000000000000000000000000000000000000000000000000000"),
    (("*", "when_dow"),     "0b1111111"),
    (("0", "when_dow"),     "0b1"),
    (("6", "when_dow"),     "0b1000000"),

    (("00,10,20,30,40,50", "when_minute"),  "0b100000000010000000001000000000100000000010000000001"),
]

date_to_bitmasksTests = [
    ((2009, 11, 6, 0, 0, 5),
        ("0b1000000000",
            "0b10000000000",
            "0b100000",
            "0b1",
            "0b1",
            "0b100000")),
    ((2009, 11, 7, 0, 0, 6),
        ("0b1000000000",
            "0b10000000000",
            "0b1000000",
            "0b1",
            "0b1",
            "0b1000000")),
    ((2009, 11, 8, 0, 0, 0),
        ("0b1000000000",
            "0b10000000000",
            "0b10000000",
            "0b1",
            "0b1",
            "0b1")),
]

if 0:
    print "WHEN_BITMASKS:"
    for when_name in WHEN_NAMES:
        print "WHEN_BITMASKS['%s'] = %s" % (when_name, bin(WHEN_BITMASKS[when_name]))
    print

if 0:
    print "WHEN_MIN_MAX:"
    for when_name in WHEN_NAMES:
        mn, mx = WHEN_MIN_MAX[when_name]
        bmMn = list_st_to_bitmask(str(mn), WHEN_MIN_MAX[when_name], WHEN_BITMASKS[when_name])
        bmMx = list_st_to_bitmask(str(mx), WHEN_MIN_MAX[when_name], WHEN_BITMASKS[when_name])
        print "WHEN_MIN_MAX['%s'] = (%s, %s) bin:(%s, %s)" % (when_name, mn, mx, bin(bmMn), bin(bmMx))
    print

if 0:
    print "list_st_to_bitmaskTests:"
    for args, expected in list_st_to_bitmaskTests:
        when_value, when_name = args
        value = bin(list_st_to_bitmask(when_value, WHEN_MIN_MAX[when_name], WHEN_BITMASKS[when_name]))
        print "when_value (%s) when_name (%s)" % (when_value, when_name)
        print "%4s: value    (%s)\n" \
            "%4s  expected (%s)" % (value == expected and "GOOD" or "FAIL", value, "", expected)
        print

if 0:
    print "date_to_bitmasksTests:"
    for args, expected in date_to_bitmasksTests:
        value = tuple([ bin(x) for x in date_to_bitmasks(*args) ])
        print "value: %s" % str(args)
        for v, e in zip(value, expected):
            print "%4s: value    (%s)\n" \
                "%4s  expected (%s)" % (v == e and "GOOD" or "FAIL", v, "", e)
        print "----"

if 1:
    print "date match tests:"
    start = datetime.datetime(2009, 11, 14, 23, 0)
    end = datetime.datetime(2009, 11, 15, 2, 0)
    delta = datetime.timedelta(minutes=1)

    #y_m_d_h_m_dow_st = ("*", "*", "*", "*", "00,10,20,30,40,50", "*")
    y_m_d_h_m_dow_st = ("*", "*", "*", "*", "*", "*")
    y_m_d_h_m_dow = tuple([ list_st_to_bitmask(x, WHEN_MIN_MAX[when_name], WHEN_BITMASKS[when_name]) \
        for x, when_name in zip(y_m_d_h_m_dow_st, WHEN_NAMES) ])
    
    print "mask mask st (%s)" % str(y_m_d_h_m_dow_st)
    print "mask mask (%s)" % str([ bin(x) for x in y_m_d_h_m_dow ])
    while start < end:
        # hcron: 0=sun, 6=sat; isoweekday: 1=mon, 7=sun
        dow = start.isoweekday() % 7
        value = date_to_bitmasks(start.year, start.month, start.day, start.hour, start.minute, dow)

        for v, e in zip(value, y_m_d_h_m_dow):
            #print "testing date (%s)" % str(start)
            if not v & e:
                break
        else:
            print "match at date (%s)" % str(start)
    
        start += delta

