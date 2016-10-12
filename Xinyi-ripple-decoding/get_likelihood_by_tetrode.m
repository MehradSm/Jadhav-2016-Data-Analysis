function [l2] = get_likelihood_by_tetrode(tet_sum, marks, mark_spikes_to_linear_position_time_bins_index_I, Xnum_I, occ_Indicator, Lint_I, dt, smker)
new_axis = ones(1, length(mark_spikes_to_linear_position_time_bins_index_I));
l0 = normpdf(marks(tet_sum, 1) * new_axis, marks(mark_spikes_to_linear_position_time_bins_index_I, 1)', smker) .* ...
    normpdf(marks(tet_sum, 2) * new_axis, marks(mark_spikes_to_linear_position_time_bins_index_I, 2)', smker) .* ...
    normpdf(marks(tet_sum, 3) * new_axis, marks(mark_spikes_to_linear_position_time_bins_index_I, 3)', smker) .* ...
    normpdf(marks(tet_sum, 4) * new_axis, marks(mark_spikes_to_linear_position_time_bins_index_I, 4)', smker);
l1 = Xnum_I * l0' ./ occ_Indicator(:, 1) ./ dt;
l2 = l1 .* dt .* exp(-Lint_I .* dt);
l2 = l2 ./ sum(l2);
end
