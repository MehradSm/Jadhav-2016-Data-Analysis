function [mark_spike_times, ...
    linear_distance_bins, ...
    linear_distance_bin_size, ...
    empirical_movement_transition_matrix, ...
    estimated_rate_all, ...
    tet_ind, ...
    tet_sum, ...
    marks, ...
    mark_spikes_to_linear_position_time_bins_index_I, ...
    smker, ...
    gaussian_kernel_position_estimator, ....
    position_occupancy, ...
    estimated_rate_by_tetrode ...
    ] = encode_state(animal, day, linear_distance, linear_position_time, state_index, tetrode_number)
%% use Loren's linearization
num_linear_distance_bins = 61;
linear_distance_bins = linspace(min(linear_distance), max(linear_distance), num_linear_distance_bins);
linear_distance_bin_size = linear_distance_bins(2) - linear_distance_bins(1);
%% empirical movement transition matrix conditioned on discrete state
num_discrete_states = length(state_index);
empirical_movement_transition_matrix = cell(num_discrete_states, 1);
for state_number = 1:num_discrete_states,
    empirical_movement_transition_matrix{state_number} = condition_empirical_movement_transition_matrix_on_state(linear_distance_bins, linear_distance, state_index{state_number});
end

%% prepare kernel density model
dt = linear_position_time(2) - linear_position_time(1);
xtrain = linear_distance';

sxker = linear_distance_bin_size;
mdel = 20;
smker = mdel;
%% encode the kernel density model per tetrode
num_tetrodes = length(tetrode_number);

mark_spike_time0 = cell(num_tetrodes, 1);
marks = cell(num_tetrodes, 1);
mark_spikes_to_linear_position_time_bins_index_by_tetrode = cell(num_tetrodes, 1);

for tetrode_ind = 1:num_tetrodes,
    [mark_spike_time0{tetrode_ind}, marks{tetrode_ind}, ...
        mark_spikes_to_linear_position_time_bins_index_by_tetrode{tetrode_ind}] = kernel_density_model(animal, day, tetrode_number(tetrode_ind), ...
        linear_position_time);
end

mark_spikes_to_linear_position_time_bins_index = cat(1, mark_spikes_to_linear_position_time_bins_index_by_tetrode{:});
%% bookkeeping code: which spike comes which tetrode
group_labels = cellfun(@(t, group) group * ones(size(t)), mark_spike_time0, num2cell(1:num_tetrodes)', 'uniformOutput', false);
group_labels = cat(1, group_labels{:});
[mark_spike_times, timeInd] = sort(cat(1, mark_spike_time0{:}));
mark_spikes_to_linear_position_time_bins_index = mark_spikes_to_linear_position_time_bins_index(timeInd, :);

tet_ind = false(length(mark_spike_times), num_tetrodes);

for tetrode_ind = 1:num_tetrodes,
    tet_ind(:, tetrode_ind) = (group_labels(timeInd) == tetrode_ind);
end

tet_sum = tet_ind .* cumsum(tet_ind,1); %row: time point; column: index of spike per tetrode

%% captial LAMBDA (joint mark intensity function) conditioned on I=1 and I=0
mark_bins = min(cat(1, marks{:})):mdel:max(cat(1, marks{:}));
estimated_rate_all = cell(num_discrete_states, 1);
position_occupancy = cell(num_discrete_states, 1);

for state_number = 1:num_discrete_states,
    [estimated_rate_all{state_number}, position_occupancy{state_number}] = condition_joint_mark_intensity_on_discrete_state(xtrain, ...
        mark_spikes_to_linear_position_time_bins_index, state_index{state_number}, ...
        sxker, mark_bins, linear_distance_bins, dt);
end

% encode per tetrode, conditioning on I=1 and I=0
mark_spikes_to_linear_position_time_bins_index_I = cell(num_tetrodes, num_discrete_states);
gaussian_kernel_position_estimator = cell(num_tetrodes, num_discrete_states);
estimated_rate_by_tetrode = cell(num_tetrodes, num_discrete_states);

for tetrode_ind = 1:num_tetrodes,
    for state_number = 1:num_discrete_states,
        [mark_spikes_to_linear_position_time_bins_index_I{tetrode_ind, state_number}, ...
            gaussian_kernel_position_estimator{tetrode_ind, state_number}, ...
            estimated_rate_by_tetrode{tetrode_ind, state_number}] = encode_per_tetrode( ...
            mark_spikes_to_linear_position_time_bins_index_by_tetrode{tetrode_ind}, ...
            state_index{state_number},  position_occupancy{state_number}, dt, ...
            linear_distance_bins, xtrain, sxker);
    end
end

save('computed_var.mat');
end