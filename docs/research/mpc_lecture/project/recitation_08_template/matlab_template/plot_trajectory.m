%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Copyright (c) 2024, Amon Lahr, Simon Muntwiler, Antoine Leeman & Fabian Flürenbrock Institute for Dynamic Systems and Control, ETH Zurich.
%
% All rights reserved.
%
% Please see the LICENSE file that has been included as part of this package.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [fig_time,axes_time,fig_pos,axes_pos] = plot_trajectory(x,u,u_info,params)
%PLOT_TRAJECTORY Summary of this function goes here
%   Detailed explanation goes here
% x,u pairs

fig_time = figure;
% get number of input trajectories

% check if input is 3-dimensional
n_traj = size(x,3);
assert(size(u,3) == n_traj);
assert(size(u_info,3) == n_traj);
    
nx = params.model.nx;
assert(nx == size(x,1));

t = 0:params.model.TimeStep:params.model.TimeStep*params.model.N_sim;

% plot
axes_time = cell(4,1);
axes_time{1} = subplot(4,1,1);
hold on;

for i = 1:n_traj
    plot(axes_time{1},t,x(1,:,i),'DisplayName','x_1');
end
legend('Location','EastOutside')

% max position
x_max = params.constraints.MaxAbsState; %*T(1);
plot(axes_time{1}, [t(1); t(end)],[x_max; x_max],'k--','HandleVisibility','off');
plot(axes_time{1}, [t(1); t(end)],[-x_max; -x_max],'k--','HandleVisibility','off');

axes_time{2} = subplot(4,1,2);
hold on;
for i = 1:n_traj
    plot(axes_time{2},t,x(2,:,i),'DisplayName','x_2');
end
legend('Location','EastOutside')

plot(axes_time{2}, [t(1); t(end)],[x_max; x_max],'k--','HandleVisibility','off');
plot(axes_time{2}, [t(1); t(end)],[-x_max; -x_max],'k--','HandleVisibility','off');

axes_time{3} = subplot(4,1,3);
hold on;
% append one input value for plotting
u(:,length(t),:) = u(:,length(t)-1,:);
for i = 1:n_traj
    stairs(axes_time{3},t,u(1,:,i)','DisplayName','u');
end

% max thrust
thrust_max = params.constraints.MaxAbsInput;
plot([t(1); t(end)],[thrust_max; thrust_max],'k--','HandleVisibility','off');
plot([t(1); t(end)],[-thrust_max; -thrust_max],'k--','HandleVisibility','off');
legend('Location','EastOutside')

% feasibility
axes_time{4} = subplot(4,1,4);
hold on;
for i = 1:n_traj
    % append one input value for plotting
    ctrl_feas = [u_info(:,:,i).ctrl_feas];
    ctrl_feas(length(t)) = ctrl_feas(length(t) - 1);
    stairs(axes_time{4},t,ctrl_feas','DisplayName',sprintf('feas_%d',i));
end
legend('Location','EastOutside')
ylabel('Feasible [0/1]')

% link axes
axes_time = [axes_time{:}];
linkaxes(axes_time,'x')
xlabel('Time [s]')
end
