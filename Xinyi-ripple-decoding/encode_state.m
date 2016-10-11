function [rippleI, ...
    ripple_index, ...
    position_time_stamps, ...
    position_time_stamps_binned, ...
    vecLF, ...
    traj_Ind, ...
    spike_times, ...
    stateV, ...
    stateV_delta, ...
    stateM_I1_normalized_gaussian, ...
    stateM_Indicator0_normalized_gaussian, ...
    Lint_I_Lambda_outbound, ...
    Lint_I_Lambda_inbound, ...
    tet_ind, ...
    tet_sum, ...
    markAll, ...
    procInd1_Ia_out, ...
    procInd1_I_out, ...
    smker, ...
    Xnum_I_out, ....
    occ_I_Lambda_outbound, ...
    Lint_I_out, ...
    procInd1_Ia_in, ...
    procInd1_I_in, ...
    Xnum_I_in, ...
    occ_I_Lambda_inbound, ...
    Lint_I_in ...
    ] = encode_state(animal, day, linpos, pos, trajencode, ripplescons, spikes, tetrode_index, neuron_index, tetrode_number)
%% use Loren's linearization
spike_times = linpos.statematrix.time;
linear_distance = linpos.statematrix.lindist;
vecLF(:,1) = spike_times;
vecLF(:,2) = linear_distance;
%figure;plot(time,linear_distance,'.');

position_time_stamps = pos.data(:,1); %time stamps for animal's trajectory
position_time_stamps_binned = round(position_time_stamps(1) * 1000):1:round(position_time_stamps(end) * 1000); %binning time stamps at 1 ms
linear_distance_bins = 61;
stateV = linspace(min(linear_distance), max(linear_distance), linear_distance_bins);
stateV_delta = stateV(2) - stateV(1);
%% calculate emipirical movement transition matrix, then Gaussian smoothed
[~, state_bin] = histc(linear_distance, stateV);
state_disM = [state_bin(1:end-1) state_bin(2:end)];
stateV_length = size(stateV,2);
%by column=departuring
for stateV_ind = 1:stateV_length
    sp0 = state_disM(state_disM(:, 1) == stateV_ind, 2); %by departure x_k-1 (by column); sp0 is the departuring x_(k-1);
    if ~isempty(sp0)
        stateM(:, stateV_ind) = histc(sp0, linspace(1, stateV_length,stateV_length)) ./ size(sp0, 1);
    else
        stateM(:, stateV_ind) = zeros(1, stateV_length);
    end
end
gaussian = @(sigma, x, y) exp(-(x.^2 + y.^2) / 2 / sigma^2); %gaussian

%%
is_outbound = find(trajencode.trajstate == 1 | trajencode.trajstate == 3);
is_inbound = find(trajencode.trajstate == 2 | trajencode.trajstate == 4);
%figure;plot(vecLF(ind_I_out,1),vecLF(ind_I_out,2),'r.',vecLF(ind_I_in,1),vecLF(ind_I_in,2),'b.');

%% empirical movement transition matrix conditioned on I=1(outbound) and I=0 (inbound)
stateV_length = length(stateV);
stateM_Indicator_outbound = zeros(stateV_length);
vecLF_seg = vecLF(is_outbound, :);
[~, state_bin] = histc(vecLF_seg(:, 2), stateV);
state_disM = [state_bin(1:end-1) state_bin(2:end)];
stateM_seg = zeros(stateV_length);
for stateV_ind=1:stateV_length
    sp0 = state_disM(state_disM(:,1) == stateV_ind, 2); %by departure x_k-1 (by column); sp0 is the departuring x_(k-1);
    if ~isempty(sp0)
        stateM_seg(:, stateV_ind) = histc(sp0, linspace(1, stateV_length, stateV_length)) ./ size(sp0, 1);
    else
        stateM_seg(:, stateV_ind) = zeros(1, stateV_length);
    end
end
stateM_Indicator_outbound = stateM_Indicator_outbound + stateM_seg;
%%%if too many zeros:
for i=1:stateV_length
    if sum(stateM_Indicator_outbound(:, i)) == 0
        stateM_Indicator_outbound(:, i) = 1 / stateV_length;
    else
        stateM_Indicator_outbound(:, i) = stateM_Indicator_outbound(:,i) ./ sum(stateM_Indicator_outbound(:, i));
    end
end

[dx, dy] = meshgrid([-1:1]);
sigma = 0.5;
normalizing_weight = gaussian(sigma, dx, dy) / sum(sum(gaussian(sigma, dx, dy))); %normalizing weights
stateM_gaussian_smoothed = conv2(stateM_Indicator_outbound, normalizing_weight, 'same'); %gaussian smoothed
stateM_I1_normalized_gaussian = stateM_gaussian_smoothed * diag(1 ./ sum(stateM_gaussian_smoothed, 1)); %normalized to confine probability to 1

stateM_Indicator_inbound = zeros(stateV_length);
vecLF_seg = vecLF(is_inbound, :);
[~,  state_bin] = histc(vecLF_seg(:, 2), stateV);
state_disM = [state_bin(1:end-1) state_bin(2:end)];
stateM_seg = zeros(stateV_length);
for stateV_ind = 1:stateV_length
    sp0 = state_disM(state_disM(:, 1) == stateV_ind, 2); %by departure x_k-1 (by column); sp0 is the departuring x_(k-1);
    if ~isempty(sp0)
        stateM_seg(:,stateV_ind) = histc(sp0, linspace(1, stateV_length, stateV_length)) ./ size(sp0, 1);
    else
        stateM_seg(:, stateV_ind) = zeros(1, stateV_length);
    end
end
stateM_Indicator_inbound = stateM_Indicator_inbound + stateM_seg;
%%if too many zeros
for i = 1:stateV_length
    if sum(stateM_Indicator_inbound(:, i)) == 0
        stateM_Indicator_inbound(:, i) = 1 / stateV_length;
    else
        stateM_Indicator_inbound(:, i) = stateM_Indicator_inbound(:, i) ./ sum(stateM_Indicator_inbound(:, i));
    end
end

[dx, dy] = meshgrid([-1:1]);
sigma = 0.5;
normalizing_weight = gaussian(sigma, dx, dy) / sum(sum(gaussian(sigma, dx, dy))); %normalizing weights
stateM_gaussian_smoothed = conv2(stateM_Indicator_inbound, normalizing_weight, 'same'); %gaussian smoothed
stateM_Indicator0_normalized_gaussian = stateM_gaussian_smoothed * diag(1 ./ sum(stateM_gaussian_smoothed, 1)); %normalized to confine probability to 1
%% calculate ripple starting and end times
ripple_start_time = ripplescons{1}.starttime;
ripple_end_time = ripplescons{1}.endtime;
traj_Ind = find(ripplescons{1}.maxthresh>4);
ripple_start_time = ripple_start_time(traj_Ind);
ripple_end_time = ripple_end_time(traj_Ind);
ripple_index = [round(ripple_start_time * 1000) - position_time_stamps_binned(1) - 1, ...
    round(ripple_end_time * 1000) - position_time_stamps_binned(1) - 1]; %index for ripple segments

for neuron_ind = 1:size(tetrode_index, 2)
    spike_times = spikes{tetrode_index(neuron_ind)}{neuron_index(neuron_ind)}.data(:,1); %spiking times for tetrode j, cell i
    binned_spike_times = round(spike_times * 1000); %binning spiking times at 1 ms
    [sptrain2_list{neuron_ind}, ~] = ismember(position_time_stamps_binned, binned_spike_times); %sptrain2: spike train binned at 1 ms instead of 33.4ms (sptrain0)
end

for k = 1:size(ripple_index,1)
    spike_r = [];
    for neuron_ind = 1:size(tetrode_index, 2)
        sptrain2 = sptrain2_list{neuron_ind};
        spike_r = [spike_r; sptrain2(ripple_index(k, 1):ripple_index(k ,2))];
    end
    spike_r_all{k} = spike_r;
end

for k = 1:size(ripple_index, 1)
    spike_r = spike_r_all{k};
    sumR(k) = sum(spike_r(:));
end
rippleI = find(sumR > 0);
%% prepare kernel density model
linear_position_time = linpos.statematrix.time;

linear_distance_bins = min(linear_distance):stateV_delta:max(linear_distance);
dt = linear_position_time(2) - linear_position_time(1);
xtrain = linear_distance';

sxker = stateV_delta;
mdel = 20;
smker = mdel;

%% encode the kernel density model per tetrode

num_tetrodes = length(tetrode_number);

markAll = cell(num_tetrodes, 1);
time0 = cell(num_tetrodes, 1);
mark0 = cell(num_tetrodes, 1);
procInd1_tet = cell(num_tetrodes, 1);

for tetrode_ind = 1:num_tetrodes,
    [markAll{tetrode_ind}, time0{tetrode_ind}, mark0{tetrode_ind}, ...
        procInd1_tet{tetrode_ind}] = kernel_density_model(animal, day, tetrode_number(tetrode_ind), ...
        linear_position_time);
end

mark0 = cat(1, mark0{:});
procInd1 = cat(1, procInd1_tet{:});
%% bookkeeping code: which spike comes which tetrode
group_labels = cellfun(@(t, group) group * ones(size(t)), time0, num2cell(1:num_tetrodes)', 'uniformOutput', false);
group_labels = cat(1, group_labels{:});
[spike_times, timeInd] = sort(cat(1, time0{:}));
mark0 = mark0(timeInd, :);
procInd1=procInd1(timeInd, :);

tet_ind = false(length(spike_times), num_tetrodes);

for tetrode_ind = 1:num_tetrodes,
    tet_ind(:, tetrode_ind) = (group_labels(timeInd) == tetrode_ind);
end

tet_sum = tet_ind .* cumsum(tet_ind,1); %row: time point; column: index of spike per tetrode

%% captial LAMBDA conditioned on I=1 and I=0
mark_bins = min(mark0(:)):mdel:max(mark0(:));
[Lint_I_Lambda_outbound, occ_I_Lambda_outbound] = condition_Lambda_on_discrete_state(xtrain, procInd1, is_outbound, sxker, mark_bins, linear_distance_bins, dt);
[Lint_I_Lambda_inbound, occ_I_Lambda_inbound] = condition_Lambda_on_discrete_state(xtrain, procInd1, is_inbound, sxker, mark_bins, linear_distance_bins, dt);

%% encode per tetrode, conditioning on I=1 and I=0
procInd1_Ia_out = cell(num_tetrodes, 1);
procInd1_Ia_in = cell(num_tetrodes, 1);
procInd1_I_out = cell(num_tetrodes, 1);
procInd1_I_in = cell(num_tetrodes, 1);
Xnum_I_out = cell(num_tetrodes, 1);
Xnum_I_in = cell(num_tetrodes, 1);
Lint_I_out = cell(num_tetrodes, 1);
Lint_I_in = cell(num_tetrodes, 1);

for tetrode_ind = 1:num_tetrodes,
    [procInd1_Ia_out{tetrode_ind}, procInd1_I_out{tetrode_ind}, Xnum_I_out{tetrode_ind}, Lint_I_out{tetrode_ind}] = encode_per_tetrode( ...
    procInd1_tet{tetrode_ind}, is_outbound,  occ_I_Lambda_outbound, dt, linear_distance_bins, xtrain, sxker);
    [procInd1_Ia_in{tetrode_ind}, procInd1_I_in{tetrode_ind}, Xnum_I_in{tetrode_ind}, Lint_I_in{tetrode_ind}] = encode_per_tetrode( ...
    procInd1_tet{tetrode_ind}, is_inbound,  occ_I_Lambda_inbound, dt, linear_distance_bins, xtrain, sxker);
end

save('computed_var.mat');
end