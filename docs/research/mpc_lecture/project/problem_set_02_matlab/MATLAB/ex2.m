%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 151-0660-00L Model Predictive Control
%
% This code is only made available for students taking the MPC class and is
% NOT to be distributed.
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

close all
clc

%% Specify the problem data
A  = [0.77, -0.35; 0.49, 0.91];
B  = [0.04; 0.15];
x0 = [1; -1];
Q  = 100 * [5, 0; 0, 1];
R  = 1;
P  = 100 * [15, 0; 0, 1];
N  = 50;

%% Generation of useful matrices
% Generation of Sx and Su matrices
Sx = eye(size(A));
Su = zeros(size(A,1)*N,size(B,2)*N);
for i=1:N
    Sx = [Sx;A^i];
    Su = Su + kron( diag( ones(N-i+1,1) , -i+1 ) , A^(i-1)*B );
end
Su = [ zeros(size(A,1),size(B,2)*N); Su ];

% Generation of the Q bar and R bar matrices
Qbar = kron([eye(N),zeros(N,1);zeros(1,N),0],Q)+...
	   kron([zeros(N,N),zeros(N,1);zeros(1,N),1],P);
Rbar = kron(eye(N),R);

%% Batch Approach
% Optimum of the batch approach
uBa    = -(Su'*Qbar*Su + Rbar)^(-1)*Su'*Qbar*Sx*x0;
costBa = x0'*(Sx'*Qbar*Sx-Sx'*Qbar*Su*(Su'*Qbar*Su+Rbar)^(-1)...
	     *Su'*Qbar*Sx)*x0;
     
%% Quadprog Approach
% Compute the matrices required for the quadratic program
Hbig = Su'*Qbar * Su + Rbar;
Fbig = Sx'*Qbar * Su;

% Make the Hessian symmetric (due to numerical issues)
Hbig = (Hbig+Hbig')/2;

% Solve the quadratic program
% Note: the factor of 2 that is required in front of `Hbig'
[Ustar, costQ] =  quadprog(2*Hbig,(2*x0'*Fbig)');
% Cost completion
costQ = costQ + x0'*Sx'*Qbar*Sx*x0;

%% Dynamic programming approach
% Set the final stage optimal cost-to-go to be the terminal cost
PRec{N+1} = P;
% Recursively step back through the horizon computing the optimal
% cost-to-go at each step
for kk=N:-1:1
    PRec{kk} = A'*PRec{kk+1}*A + Q - A'*PRec{kk+1}*B...
    	*(B'*PRec{kk+1}*B + R)^(-1)*B'*PRec{kk+1}*A;
    FRec{kk} = -(B'*PRec{kk+1}*B+R)^(-1)*B'*PRec{kk+1}*A;
end
% Optimum of the recursive approach
costRec = x0'*PRec{1}*x0;

%% Display costs
display(costBa)
display(costQ)
display(costRec)

%% Plotting the system trajecotriy
model.A = A;
model.B = B;
model.D = [0.1;0.1];
variance = 0.01;
xkp1ba = zeros(2,51);
xkp1ra = zeros(2,51);
xkp1ba(:,1) = x0;
xkp1ra(:,1) = x0;

for i = 1:N
    xkp1ba(:,i+1) = Dynamic_System(xkp1ba(:,i), uBa(i,:), model, variance);
    xkp1ra(:,i+1) = Dynamic_System(xkp1ra(:,i), FRec{i}*xkp1ra(:,i), model, variance);
end
figure
hold on
plot(xkp1ba(1,:),xkp1ba(2,:),'r','Linewidth',2);
plot(xkp1ra(1,:),xkp1ra(2,:),'k','Linewidth',2);
xlabel('x1')
ylabel('x2')
title('Comparison Batch Approach vs. Recursive Approach')
grid on
legend('batch','recursive')
hold off

%% Function definitions
function [ xkp1 ] = Dynamic_System(xk, uk, model, variance)
    xkp1 = model.A * xk + model.B*uk + model.D * sqrt(variance) * randn;
end