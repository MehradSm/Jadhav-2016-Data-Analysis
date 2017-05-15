import numpy as np
from scipy.fftpack import fft, ifft


def _conjugate_transpose(x):
    '''Conjugate transpose of the last two dimensions of array x'''
    return x.swapaxes(-1, -2).conjugate()


def _get_intial_conditions(cross_spectral_matrix):
    '''Returns a guess for the minimum phase factor'''
    return np.linalg.cholesky(
        ifft(cross_spectral_matrix, axis=-3)[..., 0:1, :, :].real
    ).swapaxes(-1, -2)


def _get_causal_signal(linear_predictor):
    '''Takes half the roots on the unit circle (zero lag) and all the roots
    inside the unit circle (positive lags)

    Gives you A_(t+1)(Z) / A_(t)(Z)
    This is the plus operator in [1]
    '''
    n_signals = linear_predictor.shape[-1]
    n_fft_samples = linear_predictor.shape[-3]
    linear_predictor_coefficients = ifft(linear_predictor, axis=-3)
    linear_predictor_coefficients[..., 0, :, :] *= 0.5
    # Form S_tau
    lower_triangular_ind = np.tril_indices(n_signals, k=-1)
    linear_predictor_coefficients[
        ..., 0, lower_triangular_ind[0], lower_triangular_ind[1]] = 0
    linear_predictor_coefficients[..., (n_fft_samples // 2) + 1:, :, :] = 0
    return fft(linear_predictor_coefficients, axis=-3)


def _check_convergence(minimum_phase_factor, old_minimum_phase_factor,
                       tolerance):
    '''Check convergence of Wilson algorithm at each time point'''
    n_time_points = minimum_phase_factor.shape[0]
    psi_error = np.linalg.norm(
        np.reshape(minimum_phase_factor - old_minimum_phase_factor,
                   (n_time_points, -1)), ord=np.inf, axis=1)
    return psi_error < tolerance


def minimum_phase_decomposition(cross_spectral_matrix, tolerance=1E-8,
                                max_iterations=30):
    '''Using the Wilson algorithm to find a minimum phase matrix square
    root of the cross spectral density'''
    n_time_points = cross_spectral_matrix.shape[0]
    n_signals = cross_spectral_matrix.shape[-1]
    I = np.eye(n_signals)
    is_converged = np.zeros(n_time_points, dtype=bool)
    minimum_phase_factor = np.zeros(cross_spectral_matrix.shape)
    minimum_phase_factor[..., :, :, :] = _get_intial_conditions(
        cross_spectral_matrix)

    for iteration in range(max_iterations):
        old_minimum_phase_factor = minimum_phase_factor.copy()
        linear_predictor = (np.linalg.solve(
            minimum_phase_factor,
            _conjugate_transpose(
                np.linalg.solve(minimum_phase_factor,
                                cross_spectral_matrix)))
                            + I)
        minimum_phase_factor = np.matmul(
            minimum_phase_factor, _get_causal_signal(linear_predictor))

        minimum_phase_factor[is_converged, ...] = old_minimum_phase_factor[
            is_converged, ...]
        is_converged = _check_convergence(
            minimum_phase_factor, old_minimum_phase_factor, tolerance)
        if np.all(is_converged):
            return minimum_phase_factor
    else:
        print('Maximum iterations reached. {} of {} converged'.format(
            is_converged.sum(), len(is_converged)))
        return minimum_phase_factor