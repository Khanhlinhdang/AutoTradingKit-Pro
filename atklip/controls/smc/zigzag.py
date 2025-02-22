import numpy as np
from numba import njit
PEAK = 1
VALLEY = -1


def identify_initial_pivot(X, up_thresh, down_thresh):
    x_0 = X[0]
    x_t = x_0
    max_x = x_0
    min_x = x_0
    max_t = 0
    min_t = 0

    up_thresh += 1
    down_thresh += 1

    for t in range(1, len(X)):
        x_t = X[t]

        if x_t / min_x >= up_thresh:
            return VALLEY if min_t == 0 else PEAK

        if x_t / max_x <= down_thresh:
            return PEAK if max_t == 0 else VALLEY

        if x_t > max_x:
            max_x = x_t
            max_t = t

        if x_t < min_x:
            min_x = x_t
            min_t = t

    t_n = len(X)-1
    return VALLEY if x_0 < X[t_n] else PEAK


def identify_initial_pivot(X, up_thresh, down_thresh):
    x_0 = X[0]
    x_t = x_0
    max_x = x_0
    min_x = x_0
    max_t = 0
    min_t = 0

    up_thresh += 1
    down_thresh += 1

    for t in range(1, len(X)):
        x_t = X[t]

        if x_t / min_x >= up_thresh:
            return VALLEY if min_t == 0 else PEAK

        if x_t / max_x <= down_thresh:
            return PEAK if max_t == 0 else VALLEY

        if x_t > max_x:
            max_x = x_t
            max_t = t

        if x_t < min_x:
            min_x = x_t
            min_t = t

    t_n = len(X)-1
    return VALLEY if x_0 < X[t_n] else PEAK



def _to_ndarray(X):
    if isinstance(X, (list, tuple)):
        X = np.array(X)
    return X


def peak_valley_pivots(X, up_thresh, down_thresh):
    X = _to_ndarray(X)

    if not str(X.dtype).startswith('float'):
        X = X.astype(np.float64)

    return peak_valley_pivots_detailed(X, up_thresh, down_thresh, True, False)


def peak_valley_pivots_detailed(X, up_thresh, down_thresh,
                                limit_to_finalized_segments,
                                use_eager_switching_for_non_final):
    if down_thresh > 0:
        raise ValueError('The down_thresh must be negative.')

    initial_pivot = identify_initial_pivot(X, up_thresh, down_thresh)
    t_n = len(X)
    pivots = np.zeros(t_n, dtype=np.int_)
    trend = -initial_pivot
    last_pivot_t = 0
    last_pivot_x = X[0]

    pivots[0] = initial_pivot

    up_thresh += 1
    down_thresh += 1

    for t in range(1, t_n):
        x = X[t]
        r = x / last_pivot_x

        if trend == -1:
            if r >= up_thresh:
                pivots[last_pivot_t] = trend
                trend = PEAK
                last_pivot_x = x
                last_pivot_t = t
            elif x < last_pivot_x:
                last_pivot_x = x
                last_pivot_t = t
        else:
            if r <= down_thresh:
                pivots[last_pivot_t] = trend
                trend = VALLEY
                last_pivot_x = x
                last_pivot_t = t
            elif x > last_pivot_x:
                last_pivot_x = x
                last_pivot_t = t

    if limit_to_finalized_segments:
        if use_eager_switching_for_non_final:
            if last_pivot_t > 0 and last_pivot_t < t_n-1:
                pivots[last_pivot_t] = trend
                pivots[t_n-1] = -trend
            else:
                pivots[t_n-1] = trend
        else:
            if last_pivot_t == t_n-1:
                pivots[last_pivot_t] = trend
            elif pivots[t_n-1] == 0:
                pivots[t_n-1] = -trend

    return pivots


def max_drawdown(X):
    X = _to_ndarray(X)

    if not str(X.dtype).startswith('float'):
        X = X.astype(np.float64)

    return max_drawdown_c(X)


def max_drawdown_c(X):
    mdd = 0
    peak = X[0]

    for x in X:
        if x > peak:
            peak = x

        dd = (peak - x) / peak

        if dd > mdd:
            mdd = dd

    return mdd if mdd != 0.0 else 0.0


def pivots_to_modes(pivots):
    modes = np.zeros(len(pivots), dtype=np.int_)
    mode = -pivots[0]

    modes[0] = pivots[0]

    for t in range(1, len(pivots)):
        x = pivots[t]
        if x != 0:
            modes[t] = mode
            mode = -x
        else:
            modes[t] = mode

    return modes

def compute_segment_returns(X, pivots):
    X = _to_ndarray(X)
    pivot_points = X[pivots != 0]
    return pivot_points[1:] / pivot_points[:-1] - 1.0
