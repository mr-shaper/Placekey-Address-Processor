// 地址公寓识别工具 - 前端交互脚本

class ApartmentProcessor {
    constructor() {
        this.currentFile = null;
        this.outputFilename = null;
        this.apiConfig = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupApiConfigHandlers();
        this.loadApiConfig();
        this.checkConfig();
    }

    setupEventListeners() {
        const uploadArea = document.getElementById('upload-area');
        const fileInput = document.getElementById('file-input');
        const processBtn = document.getElementById('process-btn');
        const downloadBtn = document.getElementById('download-btn');
        const downloadTemplateBtn = document.getElementById('download-template-btn');
        const showMappingBtn = document.getElementById('show-mapping-btn');

        // 文件拖拽
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        });

        // 点击上传
        uploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });

        // 处理和下载按钮
        processBtn.addEventListener('click', () => this.processFile());
        downloadBtn.addEventListener('click', () => this.downloadFile());
        
        // 新增功能按钮
        downloadTemplateBtn.addEventListener('click', () => this.downloadTemplate());
        showMappingBtn.addEventListener('click', () => this.toggleColumnMapping());
    }

    setupApiConfigHandlers() {
        // 切换配置面板显示
        document.getElementById('toggle-config-btn').addEventListener('click', () => {
            const configBody = document.getElementById('config-body');
            const toggleBtn = document.getElementById('toggle-config-btn');
            
            if (configBody.style.display === 'none') {
                configBody.style.display = 'block';
                toggleBtn.innerHTML = '<i class="bi bi-chevron-up"></i> 隐藏配置';
            } else {
                configBody.style.display = 'none';
                toggleBtn.innerHTML = '<i class="bi bi-chevron-down"></i> 显示配置';
            }
        });
        
        // 保存配置
        document.getElementById('config-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveApiConfig();
        });
        
        // 测试连接
        document.getElementById('test-config-btn').addEventListener('click', () => this.testApiConnection());
        
        // 清除配置
        document.getElementById('clear-config-btn').addEventListener('click', () => this.clearApiConfig());
    }

    loadApiConfig() {
        const config = this.getApiConfig();
        if (config) {
            document.getElementById('api-key').value = config.api_key || '';
            document.getElementById('api-url').value = config.api_url || 'https://api.placekey.io/v1/placekeys';
            document.getElementById('batch-size').value = config.batch_size || 100;
            document.getElementById('max-workers').value = config.max_workers || 5;
        }
    }

    getApiConfig() {
        const configStr = localStorage.getItem('apartment_api_config');
        return configStr ? JSON.parse(configStr) : null;
    }

    saveApiConfig() {
        const config = {
            api_key: document.getElementById('api-key').value,
            api_url: document.getElementById('api-url').value,
            batch_size: parseInt(document.getElementById('batch-size').value),
            max_workers: parseInt(document.getElementById('max-workers').value)
        };
        
        localStorage.setItem('apartment_api_config', JSON.stringify(config));
        this.apiConfig = config;
        
        this.showAlert('API配置已保存', 'success');
        this.checkConfig();
        
        // 自动隐藏配置面板
        setTimeout(() => {
            document.getElementById('config-body').style.display = 'none';
            document.getElementById('toggle-config-btn').innerHTML = '<i class="bi bi-chevron-down"></i> 显示配置';
        }, 1500);
    }

    testApiConnection() {
        const apiKey = document.getElementById('api-key').value;
        const apiUrl = document.getElementById('api-url').value;
        
        if (!apiKey) {
            this.showAlert('请先输入API密钥', 'warning');
            return;
        }
        
        const testBtn = document.getElementById('test-config-btn');
        testBtn.disabled = true;
        testBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 测试中...';
        
        // 发送测试请求
        fetch('/api/test-connection', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                api_key: apiKey,
                api_url: apiUrl
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showAlert('API连接测试成功', 'success');
            } else {
                this.showAlert('API连接测试失败: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            this.showAlert('连接测试失败: ' + error.message, 'danger');
        })
        .finally(() => {
            testBtn.disabled = false;
            testBtn.innerHTML = '<i class="bi bi-wifi"></i> 测试连接';
        });
    }

    clearApiConfig() {
        if (confirm('确定要清除所有API配置吗？')) {
            localStorage.removeItem('apartment_api_config');
            this.apiConfig = null;
            
            // 清空表单
            document.getElementById('config-form').reset();
            document.getElementById('api-url').value = 'https://api.placekey.io/v1/placekeys';
            document.getElementById('batch-size').value = 100;
            document.getElementById('max-workers').value = 5;
            
            this.showAlert('API配置已清除', 'info');
            this.checkConfig();
        }
    }

    async checkConfig() {
        const config = this.getApiConfig();
        const statusBadge = document.getElementById('config-status-badge');
        const toggleBtn = document.getElementById('toggle-config-btn');
        
        if (config && config.api_key) {
            statusBadge.style.display = 'inline';
            toggleBtn.innerHTML = '<i class="bi bi-chevron-down"></i> 显示配置';
            // 如果已配置，默认隐藏配置面板
            document.getElementById('config-body').style.display = 'none';
        } else {
            statusBadge.style.display = 'none';
            toggleBtn.innerHTML = '<i class="bi bi-chevron-down"></i> 显示配置';
            // 如果未配置，默认显示配置面板
            document.getElementById('config-body').style.display = 'block';
        }
    }

    async handleFile(file) {
        if (!file.name.toLowerCase().endsWith('.csv')) {
            this.showAlert('请选择CSV文件', 'warning');
            return;
        }

        if (file.size > 16 * 1024 * 1024) { // 16MB
            this.showAlert('文件大小不能超过16MB', 'warning');
            return;
        }

        this.currentFile = file;
        this.showLoading('正在读取文件...');

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.showPreview(result.preview);
                document.getElementById('file-section').style.display = 'none';
                document.getElementById('preview-section').style.display = 'block';
                this.showAlert('文件上传成功，共' + result.total_rows + '行数据', 'success');
            } else {
                this.showAlert('文件处理失败: ' + result.error, 'danger');
            }
        } catch (error) {
            this.showAlert('上传失败: ' + error.message, 'danger');
        } finally {
            this.hideLoading();
        }
    }

    showPreview(preview) {
        const table = document.getElementById('preview-table');
        const thead = table.querySelector('thead');
        const tbody = table.querySelector('tbody');
        
        // 清空表格
        thead.innerHTML = '';
        tbody.innerHTML = '';
        
        if (preview.headers && preview.headers.length > 0) {
            // 创建表头
            const headerRow = document.createElement('tr');
            preview.headers.forEach(header => {
                const th = document.createElement('th');
                th.textContent = header;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            
            // 创建数据行
            preview.rows.forEach(row => {
                const tr = document.createElement('tr');
                row.forEach(cell => {
                    const td = document.createElement('td');
                    td.textContent = cell || '';
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });
        }
    }

    async processFile() {
        if (!this.currentFile) {
            this.showAlert('请先上传文件', 'warning');
            return;
        }

        const processBtn = document.getElementById('process-btn');
        processBtn.disabled = true;
        processBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> 处理中...';
        
        this.showProgress();
        
        try {
            // 获取列映射配置
            const columnMapping = this.getColumnMapping();
            
            // 获取API配置
            const apiConfig = this.getApiConfig();
            
            const formData = new FormData();
            formData.append('file', this.currentFile);
            if (columnMapping) {
                formData.append('column_mapping', JSON.stringify(columnMapping));
            }
            if (apiConfig) {
                formData.append('api_config', JSON.stringify(apiConfig));
            }

            const response = await fetch('/api/process', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();
            
            if (result.success) {
                this.outputFilename = result.output_filename;
                this.showResults(result.stats);
                document.getElementById('results-section').style.display = 'block';
                this.showAlert('处理完成！', 'success');
            } else {
                this.showAlert('处理失败: ' + result.error, 'danger');
            }
        } catch (error) {
            this.showAlert('处理失败: ' + error.message, 'danger');
        } finally {
            this.hideProgress();
            processBtn.disabled = false;
            processBtn.innerHTML = '<i class="bi bi-gear"></i> 开始处理';
        }
    }

    getColumnMapping() {
        const mappingSection = document.getElementById('column-mapping-section');
        if (mappingSection.style.display === 'none') {
            return null;
        }
        
        const selects = mappingSection.querySelectorAll('select');
        const mapping = {};
        
        selects.forEach(select => {
            const target = select.getAttribute('data-target');
            const source = select.value;
            if (source) {
                mapping[target] = source;
            }
        });
        
        return Object.keys(mapping).length > 0 ? mapping : null;
    }

    showResults(stats) {
        document.getElementById('total-processed').textContent = stats.total_processed;
        document.getElementById('apartments-found').textContent = stats.apartments_found;
        document.getElementById('success-rate').textContent = (stats.success_rate * 100).toFixed(1) + '%';
    }

    downloadFile() {
        if (this.outputFilename) {
            window.location.href = '/api/download/' + this.outputFilename;
        }
    }

    downloadTemplate() {
        const csvContent = 'address,street_address,city,state,postal_code\n' +
                          '"123 Main St Apt 4B, New York, NY 10001","123 Main St Apt 4B","New York","NY","10001"\n' +
                          '"456 Oak Ave Unit 2A, Los Angeles, CA 90210","456 Oak Ave Unit 2A","Los Angeles","CA","90210"\n' +
                          '"789 Pine Rd Apt 1C, Chicago, IL 60601","789 Pine Rd Apt 1C","Chicago","IL","60601"';
        
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', 'apartment_address_template.csv');
        link.style.visibility = 'hidden';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        this.showAlert('CSV模板已下载', 'success');
    }

    toggleColumnMapping() {
        const mappingSection = document.getElementById('column-mapping-section');
        const showBtn = document.getElementById('show-mapping-btn');
        
        if (mappingSection.style.display === 'none') {
            this.generateColumnMapping();
            mappingSection.style.display = 'block';
            showBtn.innerHTML = '<i class="bi bi-arrow-left-right"></i> 隐藏映射';
        } else {
            mappingSection.style.display = 'none';
            showBtn.innerHTML = '<i class="bi bi-arrow-left-right"></i> 配置列映射';
        }
    }

    generateColumnMapping() {
        if (!this.currentFile) return;
        
        const container = document.getElementById('column-mapping-container');
        const table = document.getElementById('preview-table');
        const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent);
        
        const standardColumns = [
            { key: 'address', label: '完整地址' },
            { key: 'street_address', label: '街道地址' },
            { key: 'city', label: '城市' },
            { key: 'state', label: '州/省' },
            { key: 'postal_code', label: '邮编' }
        ];
        
        container.innerHTML = '';
        
        standardColumns.forEach(col => {
            const div = document.createElement('div');
            div.className = 'col-md-6 mb-3';
            
            const autoSelected = headers.find(h => 
                h.toLowerCase().includes(col.key.toLowerCase()) ||
                (col.key === 'address' && (h.includes('地址') || h.includes('Address'))) ||
                (col.key === 'city' && (h.includes('城市') || h.includes('City'))) ||
                (col.key === 'state' && (h.includes('州') || h.includes('省') || h.includes('State'))) ||
                (col.key === 'postal_code' && (h.includes('邮编') || h.includes('邮政') || h.includes('Postal') || h.includes('Zip')))
            );
            
            div.innerHTML = `
                <label class="form-label">${col.label}</label>
                <select class="form-select" data-target="${col.key}">
                    <option value="">-- 不映射 --</option>
                    ${headers.map(h => `<option value="${h}" ${h === autoSelected ? 'selected' : ''}>${h}</option>`).join('')}
                </select>
            `;
            
            container.appendChild(div);
        });
    }

    showProgress() {
        document.getElementById('progress-section').style.display = 'block';
    }

    hideProgress() {
        document.getElementById('progress-section').style.display = 'none';
    }

    showLoading(message) {
        const loading = document.getElementById('loading');
        loading.querySelector('.loading-text').textContent = message;
        loading.style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }

    showAlert(message, type = 'info') {
        const alertsContainer = document.getElementById('alerts-container');
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertsContainer.appendChild(alert);
        
        // 自动移除警告
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new ApartmentProcessor();
});