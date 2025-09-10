// 地址公寓识别工具 - 前端交互脚本

class ApartmentProcessor {
    constructor() {
        this.currentFile = null;
        this.currentFilename = null;
        this.outputFilename = null;
        this.isUploading = false;
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

        // 点击上传 - 只在非按钮区域触发
        uploadArea.addEventListener('click', (e) => {
            // 如果点击的是按钮，不触发文件选择
            if (e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                return;
            }
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
        const toggleBtn = document.getElementById('toggle-config-btn');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                const configBody = document.getElementById('config-body');
                
                if (configBody) {
                    if (configBody.style.display === 'none') {
                        configBody.style.display = 'block';
                        toggleBtn.innerHTML = '<i class="bi bi-chevron-up"></i> 隐藏配置';
                    } else {
                        configBody.style.display = 'none';
                        toggleBtn.innerHTML = '<i class="bi bi-chevron-down"></i> 显示配置';
                    }
                }
            });
        }
        
        // 保存配置
        const configForm = document.getElementById('config-form');
        if (configForm) {
            configForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveApiConfig();
            });
        }
        
        // 测试连接
        const testBtn = document.getElementById('test-config-btn');
        if (testBtn) {
            testBtn.addEventListener('click', () => this.testApiConnection());
        }
        
        // 清除配置
        const clearBtn = document.getElementById('clear-config-btn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearApiConfig());
        }
    }

    loadApiConfig() {
        const config = this.getApiConfig();
        if (config) {
            const apiKeyInput = document.getElementById('api-key');
            if (apiKeyInput) apiKeyInput.value = config.api_key || '';
            
            const apiUrlInput = document.getElementById('api-url');
            if (apiUrlInput) apiUrlInput.value = config.api_url || 'https://api.placekey.io/v1/placekeys';
            
            const batchSizeInput = document.getElementById('batch-size');
            if (batchSizeInput) batchSizeInput.value = config.batch_size || 100;
            
            const maxWorkersInput = document.getElementById('max-workers');
            if (maxWorkersInput) maxWorkersInput.value = config.max_workers || 5;
        }
    }

    getApiConfig() {
        const configStr = localStorage.getItem('apartment_api_config');
        return configStr ? JSON.parse(configStr) : null;
    }

    saveApiConfig() {
        const apiKeyInput = document.getElementById('api-key');
        const apiUrlInput = document.getElementById('api-url');
        const batchSizeInput = document.getElementById('batch-size');
        const maxWorkersInput = document.getElementById('max-workers');
        
        const config = {
            api_key: apiKeyInput ? apiKeyInput.value : '',
            api_url: apiUrlInput ? apiUrlInput.value : 'https://api.placekey.io/v1/placekeys',
            batch_size: batchSizeInput ? parseInt(batchSizeInput.value) : 100,
            max_workers: maxWorkersInput ? parseInt(maxWorkersInput.value) : 5
        };
        
        localStorage.setItem('apartment_api_config', JSON.stringify(config));
        this.apiConfig = config;
        
        this.showAlert('API配置已保存', 'success');
        this.checkConfig();
        
        // 自动隐藏配置面板
        setTimeout(() => {
            const configBody = document.getElementById('config-body');
            const toggleBtn = document.getElementById('toggle-config-btn');
            
            if (configBody) configBody.style.display = 'none';
            if (toggleBtn) toggleBtn.innerHTML = '<i class="bi bi-chevron-down"></i> 显示配置';
        }, 1500);
    }

    testApiConnection() {
        const apiKeyInput = document.getElementById('api-key');
        const apiUrlInput = document.getElementById('api-url');
        
        const apiKey = apiKeyInput ? apiKeyInput.value : '';
        const apiUrl = apiUrlInput ? apiUrlInput.value : '';
        
        if (!apiKey) {
            this.showAlert('请先输入API密钥', 'warning');
            return;
        }
        
        const testBtn = document.getElementById('test-config-btn');
        if (!testBtn) return;
        
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
            const configForm = document.getElementById('config-form');
            if (configForm) configForm.reset();
            
            const apiUrlInput = document.getElementById('api-url');
            if (apiUrlInput) apiUrlInput.value = 'https://api.placekey.io/v1/placekeys';
            
            const batchSizeInput = document.getElementById('batch-size');
            if (batchSizeInput) batchSizeInput.value = 100;
            
            const maxWorkersInput = document.getElementById('max-workers');
            if (maxWorkersInput) maxWorkersInput.value = 5;
            
            this.showAlert('API配置已清除', 'info');
            this.checkConfig();
        }
    }

    async checkConfig() {
        const config = this.getApiConfig();
        const statusBadge = document.getElementById('config-status-badge');
        const toggleBtn = document.getElementById('toggle-config-btn');
        const configBody = document.getElementById('config-body');
        
        if (config && config.api_key) {
            if (statusBadge) statusBadge.style.display = 'inline';
            if (toggleBtn) toggleBtn.innerHTML = '<i class="bi bi-chevron-down"></i> 显示配置';
            // 如果已配置，默认隐藏配置面板
            if (configBody) configBody.style.display = 'none';
        } else {
            if (statusBadge) statusBadge.style.display = 'none';
            if (toggleBtn) toggleBtn.innerHTML = '<i class="bi bi-chevron-down"></i> 显示配置';
            // 如果未配置，默认显示配置面板
            if (configBody) configBody.style.display = 'block';
        }
    }

    async handleFile(file) {
        // 防止重复上传
        if (this.isUploading) {
            console.log('DEBUG: 文件正在上传中，忽略重复请求');
            return;
        }
        
        if (!file.name.toLowerCase().endsWith('.csv')) {
            this.showAlert('请选择CSV文件', 'warning');
            return;
        }

        if (file.size > 16 * 1024 * 1024) { // 16MB
            this.showAlert('文件大小不能超过16MB', 'warning');
            return;
        }

        this.currentFile = file;
        this.isUploading = true;
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
                this.currentFilename = result.filename;
                console.log('DEBUG: 文件上传成功，保存文件名:', this.currentFilename);
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
            this.isUploading = false;
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
        console.log('DEBUG: processFile开始，currentFilename:', this.currentFilename);
        if (!this.currentFilename) {
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
            console.log('DEBUG: 获取到的API配置:', apiConfig);
            
            const requestData = {
                filename: this.currentFilename
            };
            console.log('DEBUG: 发送处理请求，数据:', requestData);
            
            if (columnMapping) {
                requestData.column_mapping = columnMapping;
            }
            if (apiConfig) {
                requestData.api_config = apiConfig;
            }

            const response = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.outputFilename = result.output_filename;
                this.showResults(result.stats);
                // 修复：使用正确的结果区域ID
        const resultSection = document.getElementById('result-section');
        if (resultSection) {
            resultSection.style.display = 'block';
        }
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
        // 修复元素ID匹配问题
        const totalRecordsElement = document.getElementById('total-records');
        const apartmentCountElement = document.getElementById('apartment-count');
        const resultSection = document.getElementById('result-section');
        
        if (totalRecordsElement) {
            totalRecordsElement.textContent = stats.total_processed || stats.total_records || 0;
        }
        
        if (apartmentCountElement) {
            apartmentCountElement.textContent = stats.apartments_found || stats.apartment_count || 0;
        }
        
        // 显示结果区域
        if (resultSection) resultSection.style.display = 'block';
    }

    downloadFile() {
        if (this.outputFilename) {
            window.location.href = '/api/download/' + this.outputFilename;
        }
    }

    downloadTemplate() {
        try {
            // 使用服务器端下载，确保跨平台兼容性
            window.location.href = '/download_template';
            this.showAlert('CSV模板下载已开始', 'success');
        } catch (error) {
            console.error('下载模板失败:', error);
            this.showAlert('下载失败，请检查浏览器设置是否允许下载文件', 'danger');
        }
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
        const progressSection = document.getElementById('progress-section');
        if (progressSection) progressSection.style.display = 'block';
    }

    hideProgress() {
        const progressSection = document.getElementById('progress-section');
        if (progressSection) progressSection.style.display = 'none';
    }

    showLoading(message) {
        const loading = document.getElementById('loading');
        if (loading) {
            const loadingText = loading.querySelector('.loading-text');
            if (loadingText) loadingText.textContent = message;
            loading.style.display = 'flex';
        }
    }

    hideLoading() {
        const loading = document.getElementById('loading');
        if (loading) loading.style.display = 'none';
    }

    showAlert(message, type = 'info') {
        const alertsContainer = document.getElementById('alerts-container');
        
        if (!alertsContainer) {
            console.warn('警告容器未找到，无法显示警告信息:', message);
            return;
        }
        
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