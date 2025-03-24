// 任务监控相关JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // 获取所有刷新状态按钮
    const statusButtons = document.querySelectorAll('.task-status-btn');

    // 为每个按钮添加点击事件
    statusButtons.forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            refreshTaskStatus(taskId);
        });
    });

    // 获取所有启动任务按钮
    const runButtons = document.querySelectorAll('.task-run-btn');

    // 为每个启动按钮添加点击事件
    runButtons.forEach(button => {
        button.addEventListener('click', function() {
            const taskId = this.getAttribute('data-task-id');
            runTask(taskId);
        });
    });

    // 自动刷新任务状态（如果页面上有任务状态元素）
    const taskStatusElements = document.querySelectorAll('[data-task-status]');
    if (taskStatusElements.length > 0) {
        // 每10秒自动刷新一次
        setInterval(function() {
            taskStatusElements.forEach(element => {
                const taskId = element.getAttribute('data-task-id');
                if (taskId) {
                    refreshTaskStatus(taskId);
                }
            });
        }, 10000);
    }
});

/**
 * 刷新任务状态
 * @param {string} taskId - 任务ID
 */
function refreshTaskStatus(taskId) {
    fetch(`/api/tasks/${taskId}/check`)
        .then(response => {
            if (!response.ok) {
                throw new Error('网络响应不正常');
            }
            return response.json();
        })
        .then(data => {
            // 更新状态显示
            updateTaskStatusDisplay(taskId, data);
        })
        .catch(error => {
            console.error('获取任务状态失败:', error);
            alert('获取任务状态失败: ' + error.message);
        });
}

/**
 * 启动WRF任务
 * @param {string} taskId - 任务ID
 */
function runTask(taskId) {
    // 禁用按钮，防止重复点击
    const button = document.querySelector(`.task-run-btn[data-task-id="${taskId}"]`);
    if (button) {
        button.disabled = true;
        button.textContent = '启动中...';
    }

    // 发送启动请求
    fetch(`/api/tasks/${taskId}/run`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('网络响应不正常');
        }
        return response.json();
    })
    .then(data => {
        // 更新状态显示
        updateTaskStatusDisplay(taskId, data);

        // 如果按钮存在，恢复按钮状态
        if (button) {
            button.textContent = '已启动';
            // 保持禁用状态，因为任务已经启动
        }
    })
    .catch(error => {
        console.error('启动任务失败:', error);
        alert('启动任务失败: ' + error.message);

        // 如果按钮存在，恢复按钮状态
        if (button) {
            button.disabled = false;
            button.textContent = '启动任务';
        }
    });
}

/**
 * 更新任务状态显示
 * @param {string} taskId - 任务ID
 * @param {Object} data - 任务数据
 */
function updateTaskStatusDisplay(taskId, data) {
    // 更新状态文本
    const statusElement = document.querySelector(`[data-task-status][data-task-id="${taskId}"]`);
    if (statusElement) {
        statusElement.textContent = data.status;

        // 根据状态设置不同的样式
        statusElement.className = 'badge';
        if (data.status === 'pending') {
            statusElement.classList.add('bg-warning');
        } else if (data.status === 'running') {
            statusElement.classList.add('bg-primary');
        } else if (data.status === 'completed') {
            statusElement.classList.add('bg-success');
        } else if (data.status === 'error') {
            statusElement.classList.add('bg-danger');
        }
    }

    // 更新消息文本
    const messageElement = document.querySelector(`[data-task-message][data-task-id="${taskId}"]`);
    if (messageElement) {
        messageElement.textContent = data.message;
    }

    // 如果任务完成，显示结果链接
    if (data.status === 'completed') {
        const resultLinkContainer = document.querySelector(`[data-result-link-container][data-task-id="${taskId}"]`);
        if (resultLinkContainer) {
            resultLinkContainer.innerHTML = `<a href="/results/${taskId}" class="btn btn-success btn-sm">查看结果</a>`;
        }
    }
}
