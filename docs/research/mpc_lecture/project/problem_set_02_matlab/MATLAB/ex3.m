clear all
close all
clc

%% Problem data
% state matrix
Ad = [0.995 0.099;-0.099 0.985]; 
% Specify the initial condition
x0 = [1; 0];
% Specify the stage cost matrix
Q = diag([2 1]);

%% Compute the magnitude of the eigenvalues of `Ad'
eigAd = eig(Ad);
abs_eigAd = abs(eigAd);
display(abs_eigAd)

%% Finite horizon cost
% Specify the time horizon
N = 100;
% Pre-allocate a matrix for storing the state evolution 
x = zeros(size(Ad,1),N+1);
% Set the initial condition as the first column
x(:,1) = x0;
% ... and compute its associated stage cost
cost_sim = x(:,1)'*Q*x(:,1);
% Iterate forwards through the time horizon
for i=2:N
    % ... autonomously evolving the state a each step
    % and storing the updated state in the next column
    x(:,i) = Ad*x(:,i-1);
    % ... and add the stage cost due to the updated state
    cost_sim = cost_sim + x(:,i)'*Q*x(:,i);
end
% Dipslay the cost that was summed from step 0 to N
display(cost_sim)

%% Infinite horizon cost
% Compute the solution of the discrete-time Lyapunov equation 
P = dlyap(Ad,Q);
% Compute the infinite horizon cost-to-go from the given intial condition
cost_lyap = x0'*P*x0;
% Display the cost
display(cost_lyap)
