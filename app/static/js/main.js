// 通用JavaScript函数

// 格式化日期时间
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
}

// 显示通知
function showNotification(message, type = 'info') {
    // 将来可以扩展为使用更复杂的通知系统
    console.log(`[${type}] ${message}`);
}

// 添加CSRF令牌到AJAX请求（如果使用Flask-WTF时需要）
function setupCSRF() {
    const token = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

    if (token) {
        fetch = (originalFetch => {
            return function(url, config) {
                config = config || {};
                config.headers = config.headers || {};

                if (config.method && config.method.toUpperCase() !== 'GET') {
                    config.headers['X-CSRFToken'] = token;
                }

                return originalFetch(url, config);
            };
        })(fetch);
    }
}

// 当DOM加载完成时执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化功能
    // setupCSRF();

    // 添加页面离开提醒（如果有未保存的表单）
    const forms = document.querySelectorAll('form[data-confirm-leave]');
    if (forms.length > 0) {
        window.addEventListener('beforeunload', function(e) {
            for (const form of forms) {
                if (form.dataset.modified === 'true') {
                    e.preventDefault();
                    e.returnValue = '有未保存的更改，确定要离开吗？';
                    return e.returnValue;
                }
            }
        });

        for (const form of forms) {
            form.addEventListener('input', function() {
                this.dataset.modified = 'true';
            });

            form.addEventListener('submit', function() {
                this.dataset.modified = 'false';
            });
        }
    }
});
