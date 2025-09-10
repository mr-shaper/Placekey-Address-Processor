# 🚀 快速使用指南

Placekey地址处理器的快速上手指南，专门用于处理地址数据，提供地址标准化、公寓识别和Placekey集成功能。

## ⚡ 5分钟快速开始

### 1. 环境准备

```bash
# 进入项目目录
cd /Users/harrison/pythonenv/projects/Placekey-Address-Processor

# 安装Python依赖
pip install -r requirements.txt

# 使用快速启动脚本（可选）
./start_processor.sh
```

### 2. 配置API密钥（必需）

```bash
# 复制环境变量模板
cp config/.env.example .env

# 编辑.env文件，添加Placekey API密钥
# PLACEKEY_API_KEY=your_api_key_here
```

**注意**: Placekey API密钥是必需的，用于获取准确的位置信息和地址标准化。

### 3. 批量处理CSV数据

#### 基础批量处理

```bash
# 使用命令行处理器
python placekey_processor.py

# 使用专用处理模块
python src/apartment_accesscode/process_user_data.py --input data/input/input_sample.csv --output data/output/output_result.csv
```

#### Web界面处理

```bash
# 启动Web服务器
python ui/app.py

# 然后在浏览器中访问 http://localhost:5001
python main.py batch -i data/input/input.csv -o data/output/output.csv --max-workers 10

# 查看处理统计报告
python process_user_data.py process -i data/input/your_data.csv -o data/output/result.csv -r data/output/report.json -v
```

#### 测试单个地址

```bash
# 测试单个地址处理效果
python process_user_data.py test-single -a "California~~~San Bernardino~~~Colton~~~2270 Cahuilla St Apt 154"
```

#### 验证识别规则

```bash
# 验证公寓识别规则是否正常工作
python process_user_data.py validate-rules
```

## 📊 数据格式说明

### 输入数据格式

您的CSV文件应包含以下列（必需列用**粗体**标注）：

- **地址** (必需) - 完整地址信息
- 收件人国家 (可选)
- 收件人省/州 (可选) 
- 收件人城市 (可选)
- 收件人邮编 (可选)
- 其他列会被保留

### 输出数据格式

处理后的CSV文件会添加以下新列：

#### 现有规则结果
- `是否公寓_原规则` - 基于现有规则的公寓判断
- `置信度_原规则` - 现有规则的置信度 (0-100)
- `匹配关键词_原规则` - 匹配到的关键词

#### Placekey增强结果（如果配置了API）
- `placekey` - Placekey标识符
- `placekey_confidence` - API返回的置信度
- `公寓类型_增强` - API识别的公寓类型
- `主地址_增强` - 标准化的主地址
- `placekey_success` - API调用是否成功

#### 整合结果
- `是否公寓_整合` - 综合判断结果
- `置信度_整合` - 综合置信度
- `匹配关键词_整合` - 综合匹配关键词
- `处理状态` - 处理状态说明
- `冲突标记` - 是否存在结果冲突

## 🎯 使用示例

### 示例1: 处理现有数据格式

假设您有如下格式的CSV文件：

```csv
收件人国家,收件人省/州,收件人城市,收件人邮编,地址,手机号,邮箱
United States,California,Grand terrace,92324,California~~~San Bernardino~~~Colton~~~2270 Cahuilla St Apt 154,(+1)6304187558,Michaiah318@gmail.com
United States,California,San diego,92115,California~~~San Diego~~~San Diego~~~4340 44th St Apt 529,(+1)6196395707,Omar19982016@gmail.com
```

处理命令：
```bash
python process_user_data.py process -i input.csv -o output.csv -v
```

### 示例2: 测试特定地址

```bash
# 测试公寓地址
python process_user_data.py test-single -a "California~~~San Bernardino~~~Colton~~~2270 Cahuilla St Apt 154"

# 测试非公寓地址
python process_user_data.py test-single -a "California~~~Los Angeles~~~Los Angeles~~~123 Main Street"
```

### 示例3: 批量处理大文件

```bash
# 先处理小样本测试
python process_user_data.py process -i large_file.csv -o test_sample.csv -s 50

# 确认结果后处理完整文件
python process_user_data.py process -i large_file.csv -o final_result.csv -r processing_report.json
```

## 🔧 高级功能

### 1. 使用原有命令行工具

```bash
# 单个地址处理
python main.py process "123 Main St Apt 4B"

# 批量处理（标准格式）
python main.py batch data/input/sample_addresses.csv data/output/output.csv

# 公寓信息分析
python main.py apartment "123 Main St Apt 4B"
```

### 2. API健康检查

```bash
# 检查Placekey API连接
python main.py health

# 显示配置信息
python main.py config
```

### 3. 运行测试

```bash
# 运行所有测试
./run.sh test

# 或手动运行
python -m pytest tests/ -v
```

## 📈 性能优化

### 处理大文件建议

1. **分批处理**: 使用 `-s` 参数先处理小样本
2. **并行处理**: 大文件会自动启用并行处理
3. **内存管理**: 超大文件会分块读取处理
4. **错误恢复**: 支持断点续传和错误重试

### 性能参考

- 小文件 (<1000条): 即时处理
- 中等文件 (1000-10000条): 1-5分钟
- 大文件 (>10000条): 自动并行处理

## 🛠️ 故障排除

### 常见问题

1. **编码问题**
   ```bash
   # 工具会自动尝试UTF-8, GBK, GB2312编码
   # 如果仍有问题，请转换文件编码为UTF-8
   ```

2. **API限制**
   ```bash
   # Placekey API有调用限制，大文件处理会自动限速
   # 可以先用现有规则处理，后续再补充API增强
   ```

3. **内存不足**
   ```bash
   # 使用分批处理
   python process_user_data.py process -i large.csv -o output.csv -s 1000
   ```

### 获取帮助

```bash
# 查看所有命令
python process_user_data.py --help

# 查看特定命令帮助
python process_user_data.py process --help
```

## 📋 识别规则说明

### 高置信度关键词 (95分)
- `apt`, `apartment`, `unit`, `suite`, `ste`
- `#` + 数字组合
- `floor`, `fl` + 数字

### 中等置信度关键词 (70-80分)
- `room`, `rm`
- `building`, `bldg`
- `tower`, `twr`

### 低置信度关键词 (50-60分)
- 单独的 `#` 符号
- `upper`, `lower`
- `front`, `rear`

### 排除规则
- 街道名称中的方向词 (North St, South Ave)
- 独立的数字编号
- 特定上下文排除

## 🎉 完成！

现在您可以开始处理现有的CSV数据了！建议先用小样本测试，确认结果符合预期后再处理完整数据。

如有问题，请检查：
1. CSV文件格式是否正确
2. 必需的"地址"列是否存在
3. 文件编码是否为UTF-8/GBK/GB2312
4. Python环境和依赖是否正确安装