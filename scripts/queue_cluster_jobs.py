#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import collections
import subprocess
sys.path.append('../src/')
import data_processing


def main():
    log_directory = '/usr3/graduate/edeno/logs'
    python_function = 'run_by_epoch.py'
    Animal = collections.namedtuple('Animal', {'directory', 'short_name'})
    num_days = 8
    days = range(1, num_days + 1)
    animals = {'HPa': Animal(directory='HPa_direct', short_name='HPa'),
               'HPc': Animal(directory='HPc_direct', short_name='HPc')
               }
    epoch_info = data_processing.make_epochs_dataframe(animals, days)
    epoch_index = (epoch_info
                   .loc[(['HPa', 'HPc'], [8]), :]
                   .loc[epoch_info.environment == 'wtr1'].index)
    for epoch in epoch_index:
        print(epoch)
        animal, day, epoch_ind = epoch
        log_file = '{animal}_{day}_{epoch}.txt'.format(
            animal=animal, day=day, epoch=epoch_ind, log_directory=log_directory)

        script = '''echo python {python_function} {animal} {day} {epoch}
                 -logfile {log_file} >/dev/null 2>&1 |
                 qsub -j y -o /dev/null -N {function_name} 2>&1'''.format(
                     python_function=python_function,
                     animal=animal,
                     day=day,
                     epoch=epoch_ind,
                     log_file=os.path.join(log_directory, log_file),
                     function_name=python_function.replace('.py', ''))

        subprocess.run(script.split(),
                       check=True,
                       universal_newlines=True,
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,
                       stdin=subprocess.PIPE)


if __name__ == '__main__':
    sys.exit(main())