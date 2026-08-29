#!/usr/bin/env python3
"""Can a hand actually make this shape?

The generator used to check only that a voicing spelled the right notes and
did not span too many frets, which let through things like guitar A-dim as
5-0-1-2-1-5: correct notes, five fretted strings across five frets, and no
hand on earth. This module is the missing constraint.

Two limits, both per instrument:

  fingers  Four, always. An open string is free, and one finger laid flat
           across several strings at the same fret is a barre and counts
           once -- but only if no OPEN string lies underneath it, because
           the barre would stop that string too.

  span     How many frets the hand covers without shifting. This is not a
           constant: a mandolin's frets are half the width of a guitar's,
           which is why 1-3-5-7 is an ordinary diminished shape there and
           a knuckle-breaker on a guitar.
"""


def groups_by_fret(frets):
    out = {}
    for string, fret in enumerate(frets):
        if fret:
            out.setdefault(fret, []).append(string)
    return out


def _contiguous(strings):
    return strings[-1] - strings[0] == len(strings) - 1


def barre_possible(frets, fret):
    """Could one finger lie flat across every string at this fret?

    Only if nothing between the outermost of them is played open: a barre
    presses those strings too, so an open string underneath it is a note
    the shape claims to sound and does not.
    """
    strings = groups_by_fret(frets).get(fret, [])
    if len(strings) < 2:
        return False
    lo, hi = min(strings), max(strings)
    return not any(frets[j] == 0 for j in range(lo, hi + 1))


def fingers_needed(frets):
    """How many fingers this shape takes. Open and muted strings are free."""
    groups = groups_by_fret(frets)
    if not groups:
        return 0

    lowest = min(groups)
    count = 0
    barred = barre_possible(frets, lowest)
    if barred:
        count += 1
    else:
        count += len(groups[lowest])

    for fret, strings in groups.items():
        if fret == lowest:
            continue
        strings = sorted(strings)
        # Two or three adjacent strings at one fret take one finger laid
        # across them; scattered ones need a finger each.
        count += 1 if len(strings) > 1 and _contiguous(strings) else len(strings)
    return count


def span(frets):
    fretted = [f for f in frets if f]
    return (max(fretted) - min(fretted)) if fretted else 0


def is_diagonal(frets):
    """One finger per string, frets climbing as the strings do.

    The hand angles across the neck for these, so they reach much further
    than a shape that asks two fingers to sit on the same string pair.
    A mandolin diminished seventh is 1-3-5-7: seven frets end to end, and
    entirely ordinary to play. The same numbers with the order jumbled
    would not be.
    """
    fretted = [(i, f) for i, f in enumerate(frets) if f]
    if len(fretted) < 2:
        return False
    # one finger per string, so no more strings than fingers
    if len(fretted) > 4:
        return False
    frets_only = [f for _, f in fretted]
    ascending = all(b > a for a, b in zip(frets_only, frets_only[1:]))
    descending = all(b < a for a, b in zip(frets_only, frets_only[1:]))
    if not (ascending or descending):
        return False

    # How steeply it climbs matters as much as how far. A diminished
    # seventh on a mandolin is 1-3-5-7: two frets per string, and the hand
    # lies across it naturally. Three frets per string covers the same
    # ground and is a different proposition entirely.
    for (i, a), (j, b) in zip(fretted, fretted[1:]):
        if abs(b - a) > 2 * (j - i):
            return False
    return True


def unplayable_reason(frets, max_span, max_fingers=4, max_diagonal=None):
    """Why a hand can't make this shape, or None if it can."""
    n = fingers_needed(frets)
    if n > max_fingers:
        return "needs %d fingers" % n
    limit = max_span
    if max_diagonal is not None and is_diagonal(frets):
        limit = max_diagonal
    s = span(frets)
    if s > limit:
        return "spans %d frets" % (s + 1)
    return None


def is_playable(frets, max_span, max_fingers=4, max_diagonal=None):
    return unplayable_reason(frets, max_span, max_fingers, max_diagonal) is None
