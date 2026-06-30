%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Copyright (c) 2024, Amon Lahr, Simon Muntwiler, Antoine Leeman & Fabian Flürenbrock Institute for Dynamic Systems and Control, ETH Zurich.
%
% All rights reserved.
%
% Please see the LICENSE file that has been included as part of this package.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [params] = generate_params()
params = struct();

% define model
params.model.TimeStep = 0.1;
params.model.N_sim  = 100;  % Number of simulation time steps
params.model.MPCHorizon = 30;   % MPC horizon length
params.model.nx = 2;
params.model.nu = 1;
params.model.InitialConditionA = [-0.7;1.4];
params.model.InitialConditionB = [0.7;1.4];

% YOUR CODE HERE

% define constraints
params.constraints.MaxAbsInput = 1;
params.constraints.MaxAbsState = 2;

% YOUR CODE HERE

end
