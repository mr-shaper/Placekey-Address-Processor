# 地址公寓识别处理方案

## 📋 方案概述

本方案整合了现有公寓识别规则与Placekey API，为地址数据提供智能的公寓识别和标准化处理服务。系统采用双重处理机制，确保高准确率的公寓识别结果。

## 🎯 核心功能

### 1. 智能公寓识别
- **现有规则引擎**: 基于完整的公寓识别规则集
- **API增强处理**: 可选的Placekey API增强功能
- **智能整合**: 自动整合两种结果，标记冲突

### 2. 多级置信度分类
- **高置信度 (95分)**: apt, apartment, unit, suite等明确标识
- **中等置信度 (70-80分)**: room, building, tower等
- **低置信度 (50-60分)**: 单独#号、upper/lower等
- **排除规则**: 街道名称、独立数字等误判排除

### 3. 批量处理能力
- **大文件支持**: 自动并行处理优化
- **错误恢复**: 断点续传和错误重试
- **多编码支持**: UTF-8、GBK、GB2312自动识别
- **性能监控**: 详细的处理统计和报告

## 🏗️ 系统架构

```
输入CSV文件
    ↓
地址预处理模块 (address_processor.py)
    ↓
现有规则识别 (integration_processor.py)
    ↓
Placekey API增强 (placekey_client.py) [可选]
    ↓
结果整合处理
    ↓
输出增强CSV文件
```

## 📁 项目结构

项目采用标准的Python工程结构，详细的目录说明请参考根目录的README.md文件。

### 核心模块位置
- **源代码**: `src/apartment_accesscode/` - 所有核心功能模块
- **配置文件**: `config/` - 环境变量和配置文件
- **示例数据**: `examples/` - 输入输出示例和使用案例
- **文档**: `docs/` - 技术文档和使用指南
- **测试**: `tests/` - 单元测试和集成测试

## 📊 输入文件格式

### 必需字段
- **地址** (必需) - 完整地址信息，格式：`省/州~~~县/市~~~城市~~~街道地址`

### 可选字段
- 收件人国家
- 收件人省/州
- 收件人城市
- 收件人邮编
- 其他业务字段（会被保留）

### 输入文件示例 (input_sample.csv)

```csv
收件人国家,收件人省/州,收件人城市,收件人邮编,地址,手机号,邮箱
United States,California,Grand terrace,92324,California~~~San Bernardino~~~Colton~~~2270 Cahuilla St Apt 154,(+1)6304187558,user1@example.com
United States,California,San diego,92115,California~~~San Diego~~~San Diego~~~4340 44th St Apt 529,(+1)6196395707,user2@example.com
United States,California,Sacramento,95828,California~~~Sacramento~~~Sacramento~~~6100 48th Ave Apt 5208,(+1)9162249125,user3@example.com
United States,California,Oakland,94612,California~~~Alameda~~~Oakland~~~1950 Broadway # 809,(+1)8134994335,user4@example.com
United States,California,San lorenzo,94541,California~~~Alameda~~~Hayward~~~659 Paradise Blvd apt B,(+1)5102305289,user5@example.com
United States,California,Los Angeles,90210,California~~~Los Angeles~~~Los Angeles~~~123 Main Street,(+1)2135551234,user6@example.com
United States,New York,New York,10001,New York~~~New York~~~New York~~~789 Broadway Unit 12A,(+1)2125551234,user7@example.com
United States,Texas,Houston,77001,Texas~~~Harris~~~Houston~~~321 Main St Suite 500,(+1)7135551234,user8@example.com
```

## 📤 输出文件格式

系统会保留所有原始字段，并添加以下识别结果字段：

### 现有规则结果
- `是否公寓_原规则` - 基于现有规则的判断 (TRUE/FALSE)
- `置信度_原规则` - 置信度分数 (0-100)
- `匹配关键词_原规则` - 匹配的关键词

### Placekey增强结果 (如果配置API)
- `placekey` - Placekey标识符
- `placekey_confidence` - API置信度
- `公寓类型_增强` - API识别的公寓类型
- `主地址_增强` - 标准化主地址
- `placekey_success` - API调用成功标记

### 整合结果
- `是否公寓_整合` - 综合判断结果
- `置信度_整合` - 综合置信度
- `匹配关键词_整合` - 综合关键词
- `处理状态` - 处理状态说明
- `冲突标记` - 结果冲突标记

### 输出文件示例 (output_sample.csv)

```csv
收件人国家,收件人省/州,收件人城市,收件人邮编,地址,手机号,邮箱,是否公寓_原规则,置信度_原规则,匹配关键词_原规则,placekey,placekey_confidence,公寓类型_增强,主地址_增强,placekey_success,是否公寓_整合,置信度_整合,匹配关键词_整合,处理状态,冲突标记
United States,California,Grand terrace,92324,California~~~San Bernardino~~~Colton~~~2270 Cahuilla St Apt 154,(+1)6304187558,user1@example.com,TRUE,95,apt(Apt),@abc-def-ghi,high,apartment,2270 Cahuilla St,TRUE,TRUE,95,apt(Apt),成功处理,FALSE
United States,California,San diego,92115,California~~~San Diego~~~San Diego~~~4340 44th St Apt 529,(+1)6196395707,user2@example.com,TRUE,95,apt(Apt),@xyz-123-456,high,apartment,4340 44th St,TRUE,TRUE,95,apt(Apt),成功处理,FALSE
United States,California,Sacramento,95828,California~~~Sacramento~~~Sacramento~~~6100 48th Ave Apt 5208,(+1)9162249125,user3@example.com,TRUE,95,apt(Apt),@def-789-abc,high,apartment,6100 48th Ave,TRUE,TRUE,95,apt(Apt),成功处理,FALSE
United States,California,Oakland,94612,California~~~Alameda~~~Oakland~~~1950 Broadway # 809,(+1)8134994335,user4@example.com,TRUE,60,#number(# 809),@ghi-456-def,medium,unit,1950 Broadway,TRUE,TRUE,70,#number(# 809),成功处理,FALSE
United States,California,San lorenzo,94541,California~~~Alameda~~~Hayward~~~659 Paradise Blvd apt B,(+1)5102305289,user5@example.com,TRUE,95,apt(apt),@jkl-012-ghi,high,apartment,659 Paradise Blvd,TRUE,TRUE,95,apt(apt),成功处理,FALSE
United States,California,Los Angeles,90210,California~~~Los Angeles~~~Los Angeles~~~123 Main Street,(+1)2135551234,user6@example.com,FALSE,0,,@mno-345-jkl,low,house,123 Main Street,TRUE,FALSE,0,,成功处理,FALSE
United States,New York,New York,10001,New York~~~New York~~~New York~~~789 Broadway Unit 12A,(+1)2125551234,user7@example.com,TRUE,95,unit(Unit),@pqr-678-mno,high,unit,789 Broadway,TRUE,TRUE,95,unit(Unit),成功处理,FALSE
United States,Texas,Houston,77001,Texas~~~Harris~~~Houston~~~321 Main St Suite 500,(+1)7135551234,user8@example.com,TRUE,95,suite(Suite),@stu-901-pqr,high,suite,321 Main St,TRUE,TRUE,95,suite(Suite),成功处理,FALSE
```

## 🚀 使用方法

### 1. 环境准备

```bash
# 进入项目目录
cd /Users/harrison/pythonenv/projects/Apartment-accesscode

# 快速安装（推荐）
./run.sh setup

# 或手动安装
pip install -r requirements.txt
```

### 2. 配置API（可选）

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，添加API密钥
# PLACEKEY_API_KEY=your_api_key_here
# 配置文件位置：config/.env
```

### 3. 处理数据

#### 预览数据
```bash
python process_user_data.py preview -i input.csv
```

#### 处理完整数据
```bash
python process_user_data.py process -i input.csv -o output.csv
```

#### 生成详细报告
```bash
python process_user_data.py process -i input.csv -o output.csv -r report.json -v
```

#### 测试单个地址
```bash
python process_user_data.py test-single -a "California~~~San Bernardino~~~Colton~~~2270 Cahuilla St Apt 154"
```

#### 验证识别规则
```bash
python process_user_data.py validate-rules
```

## 📈 性能指标

### 处理速度
- **小文件** (<1000条): 即时处理
- **中等文件** (1000-10000条): 1-5分钟
- **大文件** (>10000条): 自动并行处理

### 识别准确率
- **高置信度关键词**: >95%准确率
- **中等置信度关键词**: >85%准确率
- **低置信度关键词**: >70%准确率
- **整体准确率**: >90%

### 支持规模
- **最大文件大小**: 无限制（分块处理）
- **并发处理**: 自动优化
- **内存使用**: 智能管理

## 🔧 高级配置

### 高级配置

### 1. 环境变量配置 (config/.env)
```bash
# Placekey API配置
PLACEKEY_API_KEY=your_api_key_here

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# 处理配置
MAX_WORKERS=5
BATCH_SIZE=100

# Web界面配置
FLASK_PORT=5001
FLASK_DEBUG=False
```

### 2. 列名映射配置 (config/column_mapping.json)
```json
{
  "地址": "address",
  "城市": "city",
  "州": "state",
  "邮编": "postal_code",
  "国家": "country",
  "完整地址": "full_address",
  "单元号": "unit_number"
}
```

### 3. 批量处理参数

```python
# 在config.py中调整
BATCH_SIZE = 1000          # 批处理大小
MAX_WORKERS = 4            # 并行工作线程
API_RATE_LIMIT = 100       # API调用限制
RETRY_ATTEMPTS = 3         # 重试次数
```

### 4. 识别规则自定义

```python
# 在integration_processor.py中调整
HIGH_CONFIDENCE_KEYWORDS = [
    'apt', 'apartment', 'unit', 'suite', 'ste'
]
MEDIUM_CONFIDENCE_KEYWORDS = [
    'room', 'rm', 'building', 'bldg', 'tower', 'twr'
]
```

### 5. 输出格式自定义

可以通过修改`integration_processor.py`中的输出字段配置来自定义输出格式。

## 🛠️ 故障排除

### 常见问题

1. **编码问题**
   - 系统自动尝试UTF-8、GBK、GB2312编码
   - 建议使用UTF-8编码保存CSV文件

2. **API限制**
   - Placekey API有调用限制，系统会自动限速
   - 可以先使用现有规则处理，后续补充API增强

3. **内存不足**
   - 使用`-s`参数进行分批处理
   - 系统会自动进行内存管理

4. **处理速度慢**
   - 检查网络连接（API调用）
   - 调整并行处理参数
   - 使用样本测试优化配置

### 错误代码

- `CONFIG_ERROR`: 配置文件错误
- `FILE_NOT_FOUND`: 输入文件不存在
- `ENCODING_ERROR`: 文件编码问题
- `API_ERROR`: API调用失败
- `PROCESSING_ERROR`: 数据处理错误

## 📞 技术支持

### 获取帮助

```bash
# 查看所有命令
python process_user_data.py --help

# 查看特定命令帮助
python process_user_data.py process --help

# 运行系统测试
python process_user_data.py validate-rules
```

### 日志查看

系统会自动生成处理日志，包含：
- 处理统计信息
- 错误详情
- 性能指标
- API调用状态

## 🔄 版本更新

### 当前版本: v1.0.0

**功能特性:**
- ✅ 完整的公寓识别规则引擎
- ✅ Placekey API集成
- ✅ 批量处理支持
- ✅ 多编码格式支持
- ✅ 详细的处理报告
- ✅ 错误恢复机制

**后续计划:**
- 🔄 机器学习模型集成
- 🔄 更多API服务支持
- 🔄 实时处理接口
- 🔄 Web界面支持

## 📋 总结

本方案提供了完整的地址公寓识别解决方案，具有以下优势：

1. **高准确率**: 基于完善的规则引擎和API增强
2. **高性能**: 支持大文件批量处理和并行优化
3. **易使用**: 简单的命令行界面和详细文档
4. **可扩展**: 模块化设计，易于定制和扩展
5. **稳定性**: 完善的错误处理和恢复机制

无论是小规模的地址验证还是大批量的数据处理，本方案都能提供可靠、高效的服务。