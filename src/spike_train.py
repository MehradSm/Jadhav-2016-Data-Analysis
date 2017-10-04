import numpy as np
import pandas as pd
import xarray as xr
from patsy import build_design_matrices, dmatrix
from scipy.signal import convolve, gaussian, correlate
from scipy.stats import poisson
from statsmodels.api import GLM, families


def perievent_time_kernel_density_estimate(
        is_spike, sampling_frequency, bandwidth=30):
    '''The gaussian-smoothed kernel density estimate of firing rate over
    trials.

    Parameters
    ----------
    is_spike : ndarray, shape (n_time, n_trials)
    sampling_frequency : float
    bandwidth : float

    Returns
    -------
    firing_rate : ndarray, shape (n_time,)

    '''
    kernel = gaussian(bandwidth * 5, bandwidth)[:, np.newaxis]
    density_estimate = convolve(
        is_spike, kernel, mode='same') / kernel.sum()
    return np.nanmean(density_estimate, axis=1) * sampling_frequency


def perievent_time_spline_estimate(is_spike, time, sampling_frequency,
                                   formula='1 + bs(time, df=8, degree=3)',
                                   n_boot_samples=1000):
    design_matrix = dmatrix(formula, dict(time=time),
                            return_type='dataframe')
    fit = GLM(is_spike, design_matrix, family=families.Poisson()).fit()

    if n_boot_samples is not None:
        model_coefficients = glm_parametric_bootstrap(
            fit.params, fit.cov_params(),
            n_samples=n_boot_samples)
    else:
        model_coefficients = fit.params[:, np.newaxis]
        n_boot_samples = 1

    predict_design_matrix = build_design_matrices(
        [design_matrix.design_info], dict(time=np.unique(time)))[0]

    firing_rate_change_over_time = (
        np.exp(np.dot(predict_design_matrix, model_coefficients)) *
        sampling_frequency)
    change_over_time = np.exp(
        np.dot(predict_design_matrix[:, 1:], model_coefficients[1:]))
    baseline_firing_rate = np.exp(
        model_coefficients[0]) * sampling_frequency

    data_vars = {
        'change_over_time': (
            ['time', 'n_boot_samples'], change_over_time),
        'firing_rate_change_over_time': (
            ['time', 'n_boot_samples'], firing_rate_change_over_time),
        'baseline_firing_rate': (['n_boot_samples'], baseline_firing_rate),
    }
    coords = {'time': np.unique(time),
              'n_boot_samples': np.arange(n_boot_samples) + 1}
    return xr.Dataset(data_vars, coords)


def perievent_time_indicator_estimate(is_spike, time, sampling_frequency,
                                      formula='time', n_boot_samples=1000):
    time_indicator = np.where(time > 0, 'after0', 'before0')
    time_indicator = pd.Categorical(
        time_indicator, categories=['before0', 'after0'], ordered=True)
    design_matrix = dmatrix(
        'time', {'time': time_indicator}, return_type='dataframe')

    fit = GLM(is_spike, design_matrix, family=families.Poisson()).fit()

    if n_boot_samples is not None:
        model_coefficients = glm_parametric_bootstrap(
            fit.params, fit.cov_params(),
            n_samples=n_boot_samples)
    else:
        model_coefficients = fit.params[:, np.newaxis]
        n_boot_samples = 1

    predict_design_matrix = build_design_matrices(
        [design_matrix.design_info],
        dict(time=np.unique(time_indicator)))[0]

    firing_rate_change = -1 * np.diff(
        np.exp(np.dot(predict_design_matrix, model_coefficients)) *
        sampling_frequency, axis=0).squeeze()
    multiplicative_change = np.exp(model_coefficients[1]).squeeze()
    before0_firing_rate = np.exp(
        model_coefficients[0]) * sampling_frequency

    data_vars = {
        'multiplicative_change_after0_vs_before0': (
            ['n_boot_samples'], multiplicative_change),
        'firing_rate_change_after0_vs_before0': (
            ['n_boot_samples'], firing_rate_change),
        'before0_firing_rate': (['n_boot_samples'], before0_firing_rate),
    }
    coords = {'n_boot_samples': np.arange(n_boot_samples) + 1}
    return xr.Dataset(data_vars, coords)


def glm_parametric_bootstrap(model_coefficients, model_covariance_matrix,
                             n_samples=1000):
    return np.random.multivariate_normal(
        model_coefficients, model_covariance_matrix, n_samples).T


def cross_correlate(spike_train1, spike_train2=None, sampling_frequency=1):
    '''

    Parameters
    ----------
    spike_train1 : ndarray, shape (n_time, n_trials)
    spike_train2 : ndarray or None, shape (n_time, n_trials)
        If None, the autocorrelation of spike_train1 is computed.
    sampling_frequency : float, optional

    Returns
    -------
    cross_correlation : pandas Series

    '''
    if spike_train2 is None:
        spike_train2 = spike_train1.copy()
    correlation = np.array(
        [correlate(spike_train1_by_trial, spike_train2_by_trial)
         for spike_train1_by_trial, spike_train2_by_trial
         in zip(spike_train1.T, spike_train2.T)]).T
    correlation = np.nanmean(correlation / correlation.max(axis=0), axis=1)
    n_time = spike_train1.shape[0]
    dt = 1 / sampling_frequency
    delay = pd.Index(dt * np.arange(-n_time + 1, n_time), name='delay')
    return pd.Series(correlation, index=delay, name='correlation')


def simulate_poisson_process(rate, sampling_frequency):
    '''

    Parameters
    ----------
    rate : ndarray
    sampling_frequency : float

    Returns
    -------
    poisson_point_process : ndarray
        Same shape as rate.
    '''
    return poisson.rvs(rate / sampling_frequency)
