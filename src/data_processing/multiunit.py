from os.path import join

import numpy as np
import pandas as pd
from scipy.io import loadmat

from .core import RAW_DATA_DIR
from .tetrodes import get_trial_time


def get_multiunit_dataframe(tetrode_key, animals):
    '''Retrieve the multiunits for each tetrode given a tetrode key

    Parameters
    ----------
    tetrode_key : tuple
        Elements are (animal_short_name, day, epoch, tetrode_number)
    animals : dict of named-tuples
        Dictionary containing information about the directory for each
        animal. The key is the animal_short_name.

    Returns
    -------
    multiunit_dataframe : pandas dataframe
        The dataframe index is the time at which the multiunit occurred
        (in seconds). THe other values are values that can be used as the
        multiunits.

    '''
    TO_SECONDS = 1E4
    multiunit_file = loadmat(get_multiunit_filename(tetrode_key, animals))
    multiunit_names = [name[0][0].lower().replace(' ', '_')
                       for name in multiunit_file['filedata'][0, 0]['paramnames']]
    multiunit_data = multiunit_file['filedata'][0, 0]['params']
    multiunit_data[:, multiunit_names.index('time')] = multiunit_data[
        :, multiunit_names.index('time')] / TO_SECONDS

    return pd.DataFrame(multiunit_data, columns=multiunit_names).set_index('time')


def get_multiunit_filename(tetrode_key, animals):
    '''Path for the multiunits for a particular tetrode.

    Parameters
    ----------
    tetrode_key : tuple
        Elements are (animal_short_name, day, epoch, tetrode_number)
    animals : dict of named-tuples
        Dictionary containing information about the directory for each
        animal. The key is the animal_short_name.

    Returns
    -------
    multiunit_filename : str

    '''
    animal, day, _, tetrode_number = tetrode_key
    filename = ('{animal.short_name}marks{day:02d}-'
                '{tetrode_number:02d}.mat').format(
        data_dir=RAW_DATA_DIR,
        animal=animals[animal],
        day=day,
        tetrode_number=tetrode_number
    )
    return join(
        RAW_DATA_DIR, animals[animal].directory, 'EEG', filename)


def get_multiunit_indicator_dataframe(tetrode_key, animals,
                                      time_function=get_trial_time):
    '''A time series where a value indicates multiunit activity at that time and
    NaN indicates no multiunit activity at that time.

    Parameters
    ----------
    tetrode_key : tuple
        Elements are (animal_short_name, day, epoch, tetrode_number)
    animals : dict of named-tuples
        Dictionary containing information about the directory for each
        animal. The key is the animal_short_name.
    time_function : function, optional
        Function that take an epoch key (animal_short_name, day, epoch) that
        defines the time the multiunits are relative to. Defaults to using
        the time the LFPs are sampled at.

    Returns
    -------
    multiunit_indicator : pandas.DataFrame, shape (n_time, n_features)

    '''
    time = time_function(tetrode_key[:3], animals)
    multiunit_dataframe = (get_multiunit_dataframe(tetrode_key, animals)
                           .loc[time.min():time.max()])
    time_index = np.digitize(multiunit_dataframe.index, time)
    return (multiunit_dataframe.groupby(time[time_index]).mean()
            .reindex(index=time))
