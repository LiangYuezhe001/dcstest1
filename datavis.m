% 读取CSV数据
data = readmatrix('dcs_data.csv');

% 提取所需数据列
time_str = data(:,1);  % 时间戳
x = data(:,4);         % 原始x坐标
z = data(:,5);         % 原始y坐标
y = data(:,6);         % 原始z坐标
heading = data(:,7);   % 航向角，单位：弧度
pitch = data(:,8);     % 俯仰角，单位：弧度

% 确保数据有效
if isempty(x) || length(x) ~= length(y) || length(x) ~= length(z)
    error('数据不完整或格式错误');
end

% 创建图形窗口并确保其存在
fig = figure('Name','轨迹时间动画','Position',[100 100 1000 800]);
if ~isvalid(fig)
    fig = figure('Name','轨迹时间动画','Position',[100 100 1000 800]);
end

% 设置坐标轴范围
x_range = [min(x) max(x)];
y_range = [min(y) max(y)];
z_range = [min(z) max(z)];

% 清除当前图中可能存在的旧对象
clf(fig);

% 重新初始化轨迹线、位置点和箭头，确保对象创建成功
axes_handle = axes(fig);
hold(axes_handle, 'on');

% 初始化图形对象并检查是否创建成功
traj_line = plot3(axes_handle, NaN, NaN, NaN, 'b-', 'LineWidth', 1.5);
if ~isvalid(traj_line)
    error('无法创建轨迹线对象');
end

current_point = plot3(axes_handle, NaN, NaN, NaN, 'ro', 'MarkerSize', 8, 'LineWidth', 2);
if ~isvalid(current_point)
    error('无法创建当前位置点对象');
end

dir_arrow = quiver3(axes_handle, NaN, NaN, NaN, 0, 0, 0, 'Color', 'g', 'LineWidth', 2, 'MaxHeadSize', 0.5);
if ~isvalid(dir_arrow)
    error('无法创建方向箭头对象');
end

grid(axes_handle, 'on');
axis(axes_handle, 'equal');
axis(axes_handle, [x_range(1) x_range(2) y_range(1) y_range(2) z_range(1) z_range(2)]);

% 添加标题、标签和图例
title(axes_handle, '轨迹时间动态展示','FontSize',14);
xlabel(axes_handle, 'X坐标','FontSize',12);
ylabel(axes_handle, 'Y坐标','FontSize',12);
zlabel(axes_handle, 'Z坐标','FontSize',12);
legend(axes_handle, '轨迹','当前位置','方向','Location','best');

% 时间显示文本
time_text = annotation(fig, 'textbox', [0.05, 0.9, 0.3, 0.05], 'String', '', ...
                       'EdgeColor', 'none', 'FontSize', 12, 'BackgroundColor', [0.9 0.9 0.9]);

% 动画参数
frame_delay = 0.01;  % 每帧延迟时间（秒）
arrowLength = 500;   % 箭头长度

% 执行动画
for i = 1:length(x)
    % 检查图形对象是否仍然有效
    if ~isvalid(fig) || ~isvalid(traj_line) || ~isvalid(current_point) || ~isvalid(dir_arrow)
        error('图形对象已被删除，无法继续动画');
    end
    
    % 更新轨迹线
    traj_line.XData = x(1:i);
    traj_line.YData = y(1:i);
    traj_line.ZData = z(1:i);
    
    % 更新当前位置点
    current_point.XData = x(i);
    current_point.YData = y(i);
    current_point.ZData = z(i);
    
    % 更新方向箭头
    dx = cos(pitch(i)) * cos(heading(i));
    dy = cos(pitch(i)) * sin(heading(i));
    dz = sin(pitch(i));
    
    dir_arrow.XData = x(i);
    dir_arrow.YData = y(i);
    dir_arrow.ZData = z(i);
    dir_arrow.UData = dx * arrowLength;
    dir_arrow.VData = dy * arrowLength;
    dir_arrow.WData = dz * arrowLength;
    
    % 更新时间显示
    time_text.String = ['时间: ' num2str(time_str(i))];
    
    % 刷新图形
    drawnow;
    
    % 控制动画速度
    pause(frame_delay);
    view(axes_handle, 45, 30)
end

hold(axes_handle, 'off');
view(axes_handle, 3);  % 最终视角
