# Apartment AccessCode - 发布说明

## 版本信息
- **版本号**: v1.0.0
- **发布日期**: 2025年1月
- **状态**: 生产就绪

## 项目概述

地址公寓识别与门禁码提取工具 - 基于Placekey API的智能地址处理系统，专门用于识别公寓地址并提取门禁码(access_code)。

## 核心功能

### 🏠 智能公寓识别
- 基于规则的公寓地址识别
- 多级置信度分类系统
- 支持多种公寓格式识别

### 🔗 Placekey API集成
- 高精度地址标准化
- 地理编码和反向地理编码
- 批量处理优化

### 📊 批量处理能力
- CSV文件批量处理
- 并发处理支持
- 进度跟踪和错误处理

### 🌐 Web界面
- 直观的文件上传界面
- 实时处理进度显示
- 结果下载功能

## 技术特性

- **Python 3.8+** 支持
- **Flask** Web框架
- **pandas** 数据处理
- **Click** 命令行界面
- **多线程** 并发处理
- **配置管理** 环境变量支持

## 安装要求

```bash
# Python版本要求
Python >= 3.8

# 依赖包安装
pip install -r requirements.txt
```

## 快速开始

### 1. 环境配置
```bash
# 复制环境变量模板
cp config/.env.example .env

# 编辑配置文件
vim .env
```

### 2. 命令行使用
```bash
# 单个地址处理
python main.py single --address "123 Main St Apt 4B"

# 批量处理
python main.py batch -i input.csv -o output.csv
```

### 3. Web界面启动
```bash
# 启动Web服务
bash scripts/start_web.sh

# 访问界面
http://localhost:5001
```

## 项目结构

```
Apartment-accesscode-release/
├── src/apartment_accesscode/     # 核心模块
├── ui/                          # Web界面
├── docs/                        # 英文文档
├── CN_Introduction/             # 中文文档
├── config/                      # 配置文件
├── data/                        # 数据目录
├── examples/                    # 示例文件
├── scripts/                     # 运行脚本
├── tests/                       # 测试文件
├── main.py                      # 主程序入口
├── requirements.txt             # 依赖列表
└── setup.py                     # 安装配置
```

## 文档说明

### 中文文档 (CN_Introduction/)
- `快速开始.md` - 中文快速入门指南
- `解决方案指南.md` - 详细技术方案
- `Web界面使用指南.md` - Web界面操作说明

### 英文文档 (docs/)
- `QUICK_START.md` - English Quick Start Guide
- `SOLUTION_GUIDE.md` - Technical Solution Guide
- `WEB_UI_GUIDE.md` - Web Interface Guide

## 质量保证

✅ **代码质量检查通过**
- 语法检查无错误
- 模块导入验证通过
- 相互引用关系正确

✅ **文档完整性验证**
- 中英文文档齐全
- 链接有效性验证
- 内容一致性检查

✅ **功能测试验证**
- 核心功能模块测试
- Web界面功能测试
- 批量处理能力验证

## 许可证

MIT License - 详见 LICENSE 文件

## 支持与反馈

如有问题或建议，请通过以下方式联系：
- 邮箱：support@apartment-accesscode.com
- 项目地址：https://github.com/apartment-accesscode/apartment-accesscode

---

**发布状态**: ✅ 生产就绪，可直接部署使用