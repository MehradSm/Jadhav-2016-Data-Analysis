import numpy as np
import pandas as pd
from .core import get_data_structure
from .tetrodes import get_trial_time


def get_position_dataframe(epoch_key, animals):
    '''Returns a list of position dataframes with a length corresponding
     to the number of epochs in the epoch key -- either a tuple or a
    list of tuples with the format (animal, day, epoch_number)

    Parameters
    ----------
    epoch_key : tuple
        Defines a single epoch (animal, day, epoch)
    animals : dictionary of namedtuples
        Maps animal name to namedtuple with animal file directory

    Returns
    -------
    position : pandas dataframe
        Contains information about the animal's position, head direction,
        and speed.

    '''
    animal, day, epoch = epoch_key
    position_data = get_data_structure(animals[animal], day, 'pos', 'pos')[
        epoch - 1]['data'][0, 0]
    field_names = get_data_structure(animals[animal], day, 'pos', 'pos')[
        epoch - 1]['fields'][0, 0].item().split()
    NEW_NAMES = {'x': 'x_position',
                 'y': 'y_position',
                 'dir': 'head_direction',
                 'vel': 'speed'}
    time_index = pd.Index(
        position_data[:, field_names.index('time')], name='time')
    return (pd.DataFrame(
                position_data, columns=field_names, index=time_index)
            .rename(columns=NEW_NAMES)
            .drop([name for name in field_names
                   if name not in NEW_NAMES], axis=1))


def get_linear_position_structure(epoch_key, animals):
    animal, day, epoch = epoch_key
    struct = get_data_structure(
        animals[animal], day, 'linpos', 'linpos')[epoch - 1][0][0][
            'statematrix']
    include_fields = ['time', 'traj', 'lindist']
    new_names = {'time': 'time', 'traj': 'trajectory_category_ind',
                 'lindist': 'linear_distance'}
    return (pd.DataFrame(
        {new_names[name]: struct[name][0][0].flatten()
         for name in struct.dtype.names
         if name in include_fields})
        .set_index('time')
    )


def get_interpolated_position_dataframe(epoch_key, animals,
                                        time_function=get_trial_time):
    time = time_function(epoch_key, animals)
    position = (pd.concat(
        [get_linear_position_structure(epoch_key, animals),
         get_position_dataframe(epoch_key, animals)], axis=1)
        .assign(trajectory_direction=_trajectory_direction)
        .assign(trajectory_turn=_trajectory_turn)
        .assign(trial_number=_trial_number)
        .assign(linear_position=_linear_position)
    )
    categorical_columns = ['trajectory_category_ind',
                           'trajectory_turn', 'trajectory_direction',
                           'trial_number']
    continuous_columns = ['head_direction', 'speed',
                          'linear_distance', 'linear_position',
                          'x_position', 'y_position']
    position_categorical = (position
                            .drop(continuous_columns, axis=1)
                            .reindex(index=time, method='pad'))
    position_continuous = position.drop(categorical_columns, axis=1)
    new_index = pd.Index(np.unique(np.concatenate(
        (position_continuous.index, time))), name='time')
    interpolated_position = (position_continuous
                             .reindex(index=new_index)
                             .interpolate(method='values')
                             .reindex(index=time))
    interpolated_position.loc[
        interpolated_position.linear_distance < 0, 'linear_distance'] = 0
    interpolated_position.loc[interpolated_position.speed < 0, 'speed'] = 0
    return (pd.concat([position_categorical, interpolated_position],
                      axis=1)
            .fillna(method='backfill'))


def _linear_position(df):
    is_left_arm = (df.trajectory_category_ind == 1) | (
        df.trajectory_category_ind == 2)
    return np.where(
        is_left_arm, -1 * df.linear_distance, df.linear_distance)


def _trial_number(df):
    return np.cumsum(df.trajectory_category_ind.diff().fillna(0) > 0) + 1


def _trajectory_turn(df):
    trajectory_turn = {0: np.nan, 1: 'Left',
                       2: 'Right', 3: 'Left', 4: 'Right'}
    return df.trajectory_category_ind.map(trajectory_turn)


def _trajectory_direction(df):
    trajectory_direction = {0: np.nan, 1: 'Outbound',
                            2: 'Inbound', 3: 'Outbound', 4: 'Inbound'}
    return df.trajectory_category_ind.map(trajectory_direction)
