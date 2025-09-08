# 地址公寓识别与门禁码提取工具 - 用户使用指南

## 概述

本工具是一个专业的地址处理系统，主要功能是从地址信息中智能识别公寓单元并提取门禁码。系统采用先进的算法结合Placekey API，能够准确处理各种格式的地址数据，特别适用于房地产、物流配送、数据清洗等业务场景。

## 核心功能

### 1. 智能公寓识别
- **多格式支持**: 自动识别APT、UNIT、SUITE、#等多种公寓标识格式
- **规则引擎**: 内置智能规则引擎，能够处理复杂的地址格式
- **API增强**: 结合Placekey API进行地址标准化和验证

### 2. 门禁码提取
- **自动提取**: 从地址中自动识别和提取房号、单元号等门禁相关信息
- **格式标准化**: 将提取的信息标准化为统一格式
- **准确性验证**: 通过多重验证确保提取结果的准确性

### 3. 批量数据处理
- **高效处理**: 支持大规模CSV文件的批量处理
- **并发优化**: 采用多线程技术提升处理速度
- **进度监控**: 实时显示处理进度和状态信息

## 使用场景

### 适用行业
- **房地产管理**: 物业管理公司整理住户信息
- **快递物流**: 配送地址标准化和门禁码提取
- **数据服务**: 地址数据清洗和标准化服务
- **市场调研**: 地理位置数据分析和处理

### 典型应用
1. **住户信息管理**: 将散乱的地址信息整理为标准格式
2. **配送路线优化**: 提取准确的门禁码信息提升配送效率
3. **数据质量提升**: 清洗和标准化历史地址数据
4. **业务系统集成**: 为其他业务系统提供标准化地址数据

## 安装与配置

### 系统要求
- **操作系统**: Windows 10+、macOS 10.14+、Linux (Ubuntu 18.04+)
- **Python版本**: 3.8 或更高版本
- **内存要求**: 建议4GB以上
- **网络连接**: 需要稳定的互联网连接（用于API调用）

### 安装步骤

1. **下载项目文件**
   ```bash
   git clone [项目地址]
   cd apartment-accesscode
   ```

2. **安装依赖包**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   # 复制配置模板
   cp config/.env.example .env
   
   # 编辑配置文件
   nano .env
   ```

4. **获取API密钥**（可选但推荐）
   - 访问 [Placekey官网](https://placekey.io) 注册账户
   - 获取API密钥并添加到.env文件中
   - API密钥可提升地址识别准确性

## 使用方法

### 方法一：命令行批量处理

**基础用法**
```bash
python main.py batch -i examples/input_sample.csv -o data/output/result.csv
```

**高级参数**
```bash
# 使用中文列名映射
python main.py batch -i data/input/chinese_data.csv -o data/output/result.csv -m config/column_mapping.json

# 调整并发处理数量
python main.py batch -i data/input/large_file.csv -o data/output/result.csv --max-workers 10

# 启用详细日志
python main.py batch -i data/input/data.csv -o data/output/result.csv --verbose
```

### 方法二：Web界面操作

**启动Web服务**
```bash
python ui/app.py
```

**操作步骤**
1. 在浏览器中访问 `http://localhost:5001`
2. 上传CSV文件（支持拖拽上传）
3. 配置处理参数（可选）
4. 点击开始处理
5. 查看处理结果并下载

## 数据格式要求

### 输入文件格式
- **文件类型**: CSV格式
- **编码方式**: UTF-8（推荐）
- **必需字段**: address（地址字段）
- **可选字段**: city（城市）、state（州/省）、postal_code（邮编）

### 标准输入示例
```csv
address,city,state,postal_code
"123 Main St Apt 4B","New York","NY","10001"
"456 Oak Ave Unit 12","Los Angeles","CA","90210"
"789 Pine Rd Suite 3A","Chicago","IL","60601"
```

### 中文数据支持
系统支持中文列名，需要配置列名映射文件：
```json
{
  "地址": "address",
  "城市": "city",
  "省份": "state",
  "邮编": "postal_code"
}
```

## 输出结果说明

### 输出字段
- **原始字段**: 保留所有输入字段
- **is_apartment**: 是否为公寓地址（true/false）
- **apartment_number**: 提取的公寓号码
- **access_code**: 门禁码信息
- **confidence_score**: 识别置信度（0-1）
- **processing_status**: 处理状态

### 结果示例
```csv
address,city,state,is_apartment,apartment_number,access_code,confidence_score
"123 Main St Apt 4B","New York","NY",true,"4B","4B",0.95
"456 Oak Ave","Los Angeles","CA",false,"","",0.85
```

## 常见问题解决

### 处理速度优化
1. **调整并发数**: 根据系统性能调整`--max-workers`参数
2. **分批处理**: 将大文件分割为较小的批次
3. **网络优化**: 确保稳定的网络连接以提升API调用速度

### 准确性提升
1. **使用API密钥**: 配置Placekey API密钥可显著提升识别准确性
2. **数据预处理**: 清理输入数据中的特殊字符和格式错误
3. **字段映射**: 正确配置列名映射以确保字段识别准确

### 错误处理
1. **文件格式错误**: 确保CSV文件格式正确，使用UTF-8编码
2. **API限制**: 注意API调用频率限制，必要时降低并发数
3. **内存不足**: 处理大文件时适当增加系统内存或分批处理

## 技术支持

### 日志文件
系统运行日志保存在`logs/`目录下，包含详细的处理信息和错误记录。

### 配置文件
- **环境配置**: `config/.env`
- **列名映射**: `config/column_mapping.json`
- **Python配置**: `config/pyrightconfig.json`

### 性能监控
系统提供详细的处理统计信息，包括：
- 处理总数和成功率
- 平均处理时间
- API调用统计
- 错误分类统计

## 最佳实践

### 数据准备
1. **数据清洗**: 处理前清理明显的格式错误
2. **字段检查**: 确保必需字段完整
3. **编码统一**: 使用UTF-8编码避免乱码问题

### 批量处理
1. **合理分批**: 建议单批处理量控制在10,000条以内
2. **并发控制**: 根据系统性能和API限制调整并发数
3. **结果验证**: 处理完成后检查结果质量

### 系统维护
1. **定期更新**: 保持系统和依赖包的最新版本
2. **日志清理**: 定期清理历史日志文件
3. **配置备份**: 备份重要的配置文件

通过遵循本指南，您可以高效、准确地使用本工具处理地址数据，提升业务效率和数据质量。如有其他问题，请参考项目文档或联系技术支持。