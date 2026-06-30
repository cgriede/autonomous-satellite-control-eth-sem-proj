clear all 
close all
clc

% options for quadprog
options = optimoptions('quadprog', 'Display', 'off');

% simulation length
M = 100;

% initial conditions      
x0 = 3;

% we optimize over [x1 x2 u0 u1]'

% cost function
H = eye(4);
f = zeros(4,1);

% matrices defining the inequality constraints
A = [-1  0  0  0;
     1  0  0  0;
     0  1  0  0;
     0 -1  0  0;
     0  0  1  0;
     0  0 -1  0;
     0  0  0 -1;
     0  0  0  1];

L = 0.05;
b = [3; 3; 3; 3; L; L; L; L];

% matrices defining the equality constraints
Aeq = [  1   0  -1   0;
       -0.9   1   0  -1];
   
% state vector
x = zeros(M,1);
x(1) = x0;
J = zeros(M-1,1);

for i = 2:M

    
    beq = [0.9; 0] * x(i-1);
    
    % solving the problem via quadprog
    [xopt,FVAL,EXITFLAG,OUTPUT,LAMBDA] = quadprog(H, f, A, b, Aeq, beq, [], [], [], options);
    
    % storing the solution
    if( EXITFLAG > 0 )
        u0 = xopt(3);
        cost = 2*(FVAL + x(i-1)^2/2);
        x(i) = 0.9 * x(i-1) + u0 + 2*rand*0.3 - 0.3;
        J(i-1) = cost;
    else
        u0 = NaN;
        cost = NaN;
        disp('Infeasible');
    end
end

plot(1:(M),x);
xlabel('time step k');
ylabel('x(k)');
