clear all
close all
clc

%% Define system

% The real system is given by
% x^+ = A*x + B*u + w
%
% The nominal system by
% z^+ = A*z + B*v

% System dynamics
A = [1 1; 0 1];
B = [0.5; 1];

% System dimensions
n = length(A(1,:)); % state dimension
m = length(B(1,:)); % input dimension

% Disturbances
W = Polyhedron([1 0;-1 0;0 1;0 -1],[0.1;0.1;0.1;0.1]);

% Weighting matrices for cost function
Q = eye(2);
R = 0.01;

% State constraint set
X = Polyhedron([0 1],2);

% Input constraint set
U = Polyhedron([1;-1],[1;1]);

%% (i) Design tube-controller using LQR design

% Discrete-time Algebraic Riccati Equation
[P,~,~] = dare(A,B,Q,R);

% Discrete-time LQR controller
K_E = -1*inv(R + B.'*P*B)*B.'*P*A; %Lecture 2

% LQR closed-loop dynamics
A_c = A+B*K_E;

%equivalent to 
% K = dlqr(A,B,Q,R)
% A_c =  A-B*K_E;
%% (i) mRPI set computation
% invariant outer appoximation of the minimal robust positively invariant Set: \mathcal E (mRPI)
[ E ] = mRPI(A_c, W,6);
Ae = E.A;
be = E.b;

%% (ii) Terminal set and controller

% chose X_f = {0} --> enforce constraint z_N = 0
% no need for terminal controller design

%% (iii) Set up MPC problem and Optimizer (building an optimization problem, which can be used repeadedly)
% Set number of MPC closed-loop iterations
N_c = 20;

% Prediction horizon
N = 5;
% N = 10;
% N = 20;
% N = 30;

% Tightened state and input constraints
Xbar = X - E; %Pont. diff.
Ax_bar = Xbar.A;
bx_bar = Xbar.b;

Ubar = U - K_E*E;
Au_bar = Ubar.A;
bu_bar = Ubar.b;

% Optimization variables (Yalmip)
z_opt = sdpvar(n, N+1);
v_opt = sdpvar(m, N);
x_0 = sdpvar(n,1); % for parametrization

% Cost function (Yalmip expression)
J = 0;

% Stage costs
for i = 1:1:N
    J = J + (1/2)*(z_opt(:,i))'*Q*(z_opt(:,i)) + (1/2)*(v_opt(:,i))'*R*(v_opt(:,i));
    % no terminal cost
end

% Constraints (Yalmip expression)
constraints = [];

% System dynamics
for i = 1:1:N
    constraints = [constraints, z_opt(:,i+1) == A*z_opt(:,i) + B*v_opt(:,i)];
end

% Input constraints
for i = 1:1:N
    constraints = [constraints, Au_bar * v_opt(:,i) <= bu_bar];
end
clear('k')

% State constraints
for i = 1:1:N
    constraints = [constraints, Ax_bar * z_opt(:,i) <= bx_bar];
end

% Initial constraint
constraints = [constraints, Ae * (x_0 - z_opt(:,1)) <= be];

% Terminal constraint
constraints = [constraints, z_opt(:,N+1) == zeros(n, 1)];

% Optimization problem depending on the initial condition (the actual (measured) real state)
options = sdpsettings('solver','quadprog'); % or forces
% constraints, objective, options, parameter, output/result
MPCcontroller = optimizer(constraints, J, options, x_0, {v_opt(:,1), z_opt(:,1), J});


%% Simulation of the closed loop
% Memory allocation

% state
x = zeros(n,N_c);
x_measured = zeros(n,N_c);
z_MPC = zeros(n,N_c);

% input
u = zeros(m,N_c);
v_MPC = zeros(m,N_c);

% Initial condition of the simulation
x(:,1) = [2;1];

% loop over all time points (receding horizon)
for i = 1:(N_c-1)
    
    % measured state (Initial condition of the optimization problem)
    x_measured(:,i) = x(:,i);
    
    % Solving the MPC optimization problem and obtaining
    [solution, errorcode] = MPCcontroller{x_measured(:,i)};
    
    % First element of the optimal input trajectory
    v_MPC(:,i) = value(v_opt(:,1));
    
    % First element of the optimal state trajectory
    z_MPC(:,i) = value(z_opt(:,1));
    
    % Application of the Tube MPC control law (MPC + local LQR)
    u(:,i) = v_MPC(:,i) + K_E * (x(:,i) - z_MPC(:,i));
    
    
    % Disturbance at this iteration (random point in W)
    w_min = -0.1;
    w_max = 0.1;
    w = w_min + (w_max - w_min) .* rand(n,1);
    
    % Real system
    x(:,i+1) = A*x(:,i) + B*u(:,i) + w;
    clear('w')
    
end


%% Plots
% Plot the states of the real (disturbed) system and the sequence of the
% initial states of the nominal system
figure(2), clf, hold on,
for i = 1:(N_c-1)
    plot(E+z_MPC(:,i),'color',[0.5 0.5 0.5])
end
plot_state = plot(x(1,:),x(2,:),'LineWidth',2);
plot_nominal_state = plot(z_MPC(1,:),z_MPC(2,:),'g-.','LineWidth',2);
plot(0,0,'.','color','black')
title('state space')
legend([plot_state,plot_nominal_state],'state','nominal state','Location','northwest')
xlabel('x_1')
ylabel('x_2')

% Plot the inputs
Ubar = Ubar.minHRep();
figure(3), clf
yline(-1);
hold on
yline(-Ubar.b(2),'--');
stairs(u,'LineWidth',2);
stairs(v_MPC,'g','LineWidth',2);
yline(1);
yline(Ubar.b(1),'--');
title('input')
legend('constraints','tightened constraints','input','nominal input')
xlabel('iteration')
ylabel('u')
ylim([-1.1,1.1])
xlim([1,N_c])

%% (iv) Approximate feasible set
figure(4);
hold on;
x1 = linspace(-10,10,50);
x2 = linspace(-10,3,50);
xfeas = [];
for i=1:1:length(x1)
    for ii = 1:1:length(x2)
        % sample from state space
        x0 = [x1(i); x2(ii)];
        % test if feasible
        [~, errorcode] = MPCcontroller{x0};
        if errorcode == 0
            xfeas(:,end+1) = x0;
        end 
    end
end
% plot(X);
X_N = Polyhedron(xfeas');
plot(X_N,'color','g');
title('approximate feasible set')
xlabel('x_1')
ylabel('x_2')
