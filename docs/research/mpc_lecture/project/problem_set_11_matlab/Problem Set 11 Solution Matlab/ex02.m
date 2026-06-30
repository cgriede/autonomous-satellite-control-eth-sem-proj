%% Problem set - MPC lecture

clear all;
close all;
clc;

Q = [1,0;0,2];
L = max(eig(Q));
v = [2;3];
f = @(x1,x2) (x1-v(1)).*Q(1,1).*(x1-v(1)) + (x2-v(2)).*Q(2,2).*(x2-v(2));
df = @(x) Q*(x-v);
r = 1;
x0 = [5;5];

[x1,x1_bp] = grad_proj(x0, df,L,r);


plot(x1(1,:),x1(2,:),'*-','Linewidth',2);
hold on;
plot(x1_bp(1,:),x1_bp(2,:),'*-','Linewidth',2);
grid on;
phi = 0:0.01:2*pi;
plot(r*sin(phi), r*cos(phi),'k--');
[X,Y]=meshgrid(-5:0.01:5);
z = f(X,Y);
contour(X,Y,z,[1:15]);
axis equal

function [x, x_bp] = grad_proj(x0, df,L,r)

    N = 100;
    x = nan(2,N);
    x_bp = nan(2,N);
    
    x(:,1) = x0;
    for i = 1:N     
       x(:,i+1) = x(:,i) - 1/L*df(x(:,i));
       x_bp(:,i) = x(:,i+1);
       if norm(x(:,i+1))>r
           x(:,i+1) = r*x(:,i+1)/norm(x(:,i+1));
       end
    end

end