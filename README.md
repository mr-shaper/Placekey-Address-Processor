# Placekey Address Processor / Placekey地址处理器

[English](#english) | [中文](#中文)

---

## English

### Overview
A powerful Python application for processing apartment addresses with Placekey integration. This tool provides address standardization, apartment type identification, and batch processing capabilities through both command-line and web interfaces.

### Key Features
- **Address Standardization**: Normalize and validate address formats
- **Apartment Detection**: Intelligent identification of apartment types and units
- **Placekey Integration**: Seamless integration with Placekey API for location intelligence
- **Batch Processing**: Handle large datasets efficiently
- **Web Interface**: User-friendly web UI for easy operation
- **Flexible Output**: Multiple output formats and customizable column mapping

### Quick Start

#### Requirements
- Python 3.8+
- Placekey API key (optional for enhanced functionality)

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment
```bash
# Copy configuration template
cp config/.env.example config/.env
# Edit .env file and add your Placekey API key
```

#### Basic Usage
```bash
# Batch process CSV files
python main.py batch -i examples/input_sample.csv -o data/output/result.csv
```

### Documentation

- [📖 **Quick Start Guide**](docs/QUICK_START.md) - Get started quickly
- [🔧 **Solution Guide**](docs/SOLUTION_GUIDE.md) - Advanced configuration and solutions
- [🌐 **Web UI Guide**](docs/WEB_UI_GUIDE.md) - Web interface usage instructions
- [👤 **用户使用指南 (Chinese)**](CN_Introduction/USER_GUIDE.md) - Complete usage guide in Chinese

---

## 中文

基于Placekey API的智能地址处理系统，专门用于识别地址中的公寓信息并提取门禁码。

## 项目特点

- 🏠 **智能公寓识别**: 结合规则引擎和Placekey API双重验证
- 🔑 **门禁码提取**: 自动识别和提取地址中的门禁码信息
- 📊 **批量处理**: 支持CSV文件批量处理，适合大规模数据处理
- 🌐 **Web界面**: 提供友好的Web操作界面
- 🔧 **灵活配置**: 支持自定义字段映射和处理参数

## 快速开始

### 环境要求
- Python 3.8+
- Placekey API密钥

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境
```bash
# 复制配置文件模板
cp config/.env.example .env
# 编辑.env文件，添加你的Placekey API密钥
```

### 基本使用
```bash
# 批量处理CSV文件
python main.py batch -i examples/input_sample.csv -o data/output/result.csv
```

### 相关文档

- [👤 **用户使用指南**](CN_Introduction/USER_GUIDE.md) - 完整的使用说明和最佳实践
- [⚡ 快速开始指南](CN_Introduction/QUICK_START.md) - 快速上手教程
- [🔧 解决方案指南](CN_Introduction/SOLUTION_GUIDE.md) - 高级配置和解决方案
- [🌐 Web界面指南](CN_Introduction/WEB_UI_GUIDE.md) - Web界面使用说明
- [📖 **English Documentation**](docs/) - Complete English documentation

---

## Project Structure | 项目结构

```
apartment-accesscode/
├── CN_Introduction/       # 中文文档目录 (Chinese Documentation)
│   ├── USER_GUIDE.md     # 用户使用指南
│   ├── QUICK_START.md    # 快速开始指南
│   ├── SOLUTION_GUIDE.md # 解决方案指南
│   └── WEB_UI_GUIDE.md   # Web界面使用指南
├── config/               # 配置文件目录 (Configuration)
│   ├── .env.example     # 环境变量模板
│   ├── column_mapping.json # 列名映射配置
│   └── pyrightconfig.json # Python类型检查配置
├── data/                 # 数据目录 (Data Directory)
│   ├── input/           # 输入数据
│   └── output/          # 输出结果
├── docs/                 # 英文文档目录 (English Documentation)
│   ├── QUICK_START.md   # Quick Start Guide
│   ├── SOLUTION_GUIDE.md # Solution Guide
│   └── WEB_UI_GUIDE.md  # Web UI Guide
├── examples/             # 示例文件 (Example Files)
│   ├── input_sample.csv # 示例输入文件
│   ├── output_sample.csv # 示例输出文件
│   └── usage_examples.py # 使用示例代码
├── logs/                 # 日志文件 (Log Files)
├── scripts/              # 脚本文件 (Scripts)
├── src/                  # 源代码 (Source Code)
├── tests/                # 测试文件 (Tests)
├── ui/                   # Web界面 (Web Interface)
├── main.py              # 主程序入口 (Main Entry)
├── requirements.txt     # 依赖包列表 (Dependencies)
└── setup.py            # 安装配置 (Setup Configuration)
```

## 📄 许可证

MIT License