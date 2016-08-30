# Sure, but for Python programmers that's not how it would be done.  In
# a general-purpose language, you would use the type system.  It would
# be done like this (only better, I just don't feel like writing out a
# whole suite of math dunders):

    # If I remember my 1976 EE course correctly:
# one of several ways to compute power.
class Quantity:
    def __init__(self, value):
        self.value = value
    def __float__(self):
        return self.value

class Potential(Quantity):
    pass

class Current(Quantity):
    pass

class Resistance(Quantity):
    pass

class Power(Quantity):
    pass

def power2(potential: Potential, resistance: Resistance) -> Power:
    # Consenting adults!  Ie, we trust programmers to get this formula
    # right, do the computation without units (types), and provide
    # the correct unit (type) on the way out.
    return Power(float(potential) ** 2 / float(resistance))

ohms = Resistance(2)
volts = Potential(10)
amperes = Current(6)

watts = power2(ohms, volts)                # arguments reversed
watts = power2(volts, amperes)             # wrong type argument 2

#     # in module ee
#     import quantity
#     from quantity import Quantity
 #
#     quantity.register(type=ee.Current, fix='post', notation='A')
#     quantity.reg
ister(type=ee.Potential, sfix='post', notation='V')
#
#     # in module spicy
#     from ee import Quantity as Q
#
#     amperes = Q("6e-3A")
#     volts = Q("6mV")

# It's just that it would force you to stop
# being lazy once in a while when you run into a new parameter with
# wacko units.

# As for "V = I", a sufficiently smart circuit simulator would color
# that equation in red and prompt "Shall I multiply by 1.0 mhos? [y/n]".
# Or autocomplete to "V = I * 1mho" on enter, and flash the autoinserted
# factor a couple times to make sure you notice, so you can correct it
# if it's wrong.  I bet you would get used to that quickly enough.  (If
# there are multiple such factors, it could make up units like
# Deutschemark-volts/mole.)  Of course, for those using Spice since
# 1974, there's a --suppress-trivial-factors-and-their-units option.

# One idea for output formatting would be to keep a list of SI scale
# factors ever used in the computation, and use the closest one.  I
# bet this would be an effective heuristic.
