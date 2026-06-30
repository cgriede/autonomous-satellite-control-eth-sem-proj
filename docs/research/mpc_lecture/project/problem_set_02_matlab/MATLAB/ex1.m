%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% 151-0660-00L Model Predictive Control
%
% This code is only made available for students taking the MPC class and is
% NOT to be distributed.
%
% This is the implementation of the example given in pag.20 of the book:
% Model Predictive Control: Theory and Design of James B. Rawlings and
% David Q. Mayne
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

clc
close all

%% Part A: finite horizon controller

% System matrices
A = [4/3, -2/3; 1, 0];
B = [1; 0];
C = [-2/3, 1];

% Cost Matrices
Q = C' * C + 0.001 * eye(2);
R = 0.001;

% Prediction horizon (try e.g. 5, 7, 9)
N = 5;

% Initial state
x0 = [10; 10];

fprintf('Prediction horizon : %i\n', N);

% Compute via DP
fprintf('Computing controller via dynamic programming\n');

% initialization for P
P = Q;
for i = N:-1:1

    % Linear Feedback
    % Note: In Matlab x = A\b is recommended over x = inv(A)*b for
    % solving systems of linear equations.
    K = -(R+B'*P*B)\B'*P*A;

    % Riccati update
    % Note: this is an alternative but equivalent form of the known
    % equation P = A'*P*A + Q - A'*P*B*inv(B'*P*B + R)*B'*P*A.
    % This alternative form of the Ricatti Difference Equation is more
    % suitable from a numerical perspective as no inverse needs to be
    % computed and the symmetry of P is enforced.
    P = Q + K'*R*K + (A+B*K)'*P*(A+B*K);

    % Store the future feedback laws so that
    % we can later plot the prediction
    Kpred{i} = K;
end


% Simulate closed-loop dynamic
figure(1)
x(:,1) = x0;
i = 1;
while 1
    % checking the exit conditions
    if norm(x(:,i)) > 3*norm(x0), fprintf('===> System unstable\n'); break; end
    if norm(x(:,i)) < 5e-2,       fprintf('===> System stable\n');   break; end

    % updating the system
    u(:,i)   = K*x(:,i);
    x(:,i+1) = A*x(:,i) + B*u(:,i);

    % computing the simulated prediction
    x_pred   = compute_prediction(x(:,i), Kpred, A, B);

    % plot of the trajecotries
    clf;
    hold on;
    plot(x_pred(1,:), x_pred(2,:), '-o');
    plot(x(1,1:i) , x(2,1:i) , 'LineWidth',1.5);
    hold off;
    grid on;
    legend('Prediction','Closed Loop System');
    title('State Space');

    pause(0.1)
    i = i + 1;
end
y = C*x;

% Final Plot
figure(2)

subplot(2,2,1);
plot(u,'-*');
title('u');
grid on;

subplot(2,2,3);
plot(y,'-*');
title('y');
grid on;

subplot(2,2,[2,4]);
plot(x(1,:),x(2,:),'-o');
title('x');
xlabel('x1');
ylabel('x2');
grid on;


%% Part B: infinite horizon controller
[Klqr,~,~] = dlqr(A, B, Q, R); % compute LQR feedback law

costlqr = compute_cost(x0, A-B*Klqr, Klqr , Q, R, 1000);
costPn  = compute_cost(x0, A+B*K,    K    , Q, R, 1000);

fprintf('Cost of the optimal LQR controller : %.2f\n', costlqr);
fprintf('Cost of the N-step controller      : %.2f\n', costPn);


%% Function definitions
% Simulate the closed-loop system and compute the cost
function cost = compute_cost(x0, Ak, K, Q, R, steps)

cost = 0;
x = x0;
for i=1:steps
    cost = cost + x'*(Q+K'*R*K)*x;
    x = Ak*x;
end

end

% Compute the prediction
function x = compute_prediction(x0, K, A, B)

x(:,1) = x0;
for i = 1:length(K)
    x(:,i+1) = (A + B*K{i})*x(:,i);
end

end
