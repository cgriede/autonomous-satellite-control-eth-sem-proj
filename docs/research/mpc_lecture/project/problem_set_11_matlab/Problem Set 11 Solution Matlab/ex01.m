%% Problem set - MPC lecture

clear all;
close all;
clc

f = @(x) -exp(-x.^2);
df = @(x) 2*exp(-x.^2).*x;
ddf = @(x) exp(-x.^2).*(2-4.*x.^2);
delta_x = @(x) df(x)/ddf(x);

x0 = NM(0.5, df, ddf);
x1 = NM(0.45, df, ddf);
x2 = NM(0.4, df, ddf);
x3 = NM(sqrt(2)/2-0.1, df, ddf);
figure(1);
clf;
sgtitle('Descent method for the minimum of f(x) = -e^{-x^2}');
subplot(1,2,1);
vec =linspace(-.5, 0.5);
semilogy(vec, f(vec), 'k-', 'LineWidth', 1)
hold on
grid on;
semilogy(x0, f(x0), '*-', 'LineWidth', 2);
semilogy(x1, f(x1), '*-', 'LineWidth', 2);
semilogy(x2, f(x2), '*-', 'LineWidth', 2);
legend('f(x)','x_0 = 0.5','x_0 = 0.45','x_0 = 0.4')
xlabel('x')
ylabel('f(x)')
title('Newton Method')

x4 = GD(0.2, df, 0.1);
x5 = GD(-1, df, 0.5);
x6 = GD(0.5, df, 0.1);
x7 = GD(-0.7, df, 1);
subplot(1,2,2);
vec =linspace(-1, .5);
semilogy(vec, f(vec), 'k-', 'LineWidth', 1)
hold on;
grid on;

semilogy(x4, f(x4), '*-', 'LineWidth', 2);
semilogy(x5, f(x5), '*-', 'LineWidth', 2);
semilogy(x6, f(x6), '*-', 'LineWidth', 2);
semilogy(x7, f(x7), '*-', 'LineWidth', 2);

legend('f(x)','x_0 = 0.2, h = 0.1','x_0 = -1, h = 0.5','x_0 = 0.5, h = 0.1','x_0 = -0.7, h = 1');
xlabel('x')
ylabel('f(x)')
title('Gradient method')



x = 0:0.001:3;
D_x = -df(x)./ddf(x);
G_x = -df(x);
figure(2);
clf;
semilogy(x(D_x>0), D_x(D_x>0), 'LineWidth', 2)
hold on;
grid on;
semilogy(x(D_x<0), -D_x(D_x<0), 'LineWidth', 2)
semilogy(x, -G_x, 'LineWidth', 2)

legend('\Delta {x_{nt}} >0', '\Delta {x_{nt}} <0', '\Delta {x_{gd}}');
xlabel('x_n');
ylabel('\Delta x_n');
sgtitle('Step size for the Newton method with f(x) = -e^{-x^2}');

figure(3);
clf;
subplot(2,1,1);
it = 1:5;
semilogy(it,abs(x5(it)),'*-' ,it,abs(x6(it)),'*-' ,'LineWidth', 2);
grid on;
title('Gradient descent');
ylabel('x_i');
xlabel('iteration');

subplot(2,1,2);
semilogy(1:1:101,abs(x1),'*-' ,1:1:101,abs(x2),'*-' ,'LineWidth', 2);
title('Newton method');
grid on;
ylabel('x_i');
xlabel('iteration');

function x = NM(x0, df, ddf)

    N = 100;
    x = nan(N,1);
    x(1) = x0;
    for i = 1:N
       x(i+1) = x(i) - df(x(i))/ddf(x(i));
    end

end


function x = GD(x0, df, h)

    N = 100;
    x = nan(N,1);
    x(1) = x0;
    for i = 1:N
       x(i+1) = x(i) - h* df(x(i));
    end

end

