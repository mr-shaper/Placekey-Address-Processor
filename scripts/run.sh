#!/bin/bash
# -*- coding: utf-8 -*-

# Placekey地址标准化工具 - 快速启动脚本
# 使用方法: ./run.sh [command] [options]

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Python环境
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装，请先安装Python3"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_info "Python版本: $python_version"
    
    if [[ "$python_version" < "3.7" ]]; then
        print_error "需要Python 3.7或更高版本"
        exit 1
    fi
}

# 检查并创建虚拟环境
setup_venv() {
    if [ ! -d "venv" ]; then
        print_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    print_info "激活虚拟环境..."
    source venv/bin/activate
    
    print_info "升级pip..."
    pip install --upgrade pip
}

# 安装依赖
install_deps() {
    print_info "安装项目依赖..."
    pip install -r requirements.txt
    
    print_success "依赖安装完成"
}

# 检查环境变量
check_env() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_warning "未找到.env文件，正在从.env.example创建..."
            cp .env.example .env
            print_info "请编辑.env文件并设置您的API密钥"
        else
            print_warning "未找到环境配置文件"
        fi
    fi
    
    # 检查API密钥
    if [ -z "$PLACEKEY_API_KEY" ] && ! grep -q "PLACEKEY_API_KEY=" .env 2>/dev/null; then
        print_warning "未设置PLACEKEY_API_KEY，部分功能可能无法使用"
        print_info "请在.env文件中设置: PLACEKEY_API_KEY=your_api_key"
    fi
}

# 运行测试
run_tests() {
    print_info "运行测试..."
    
    if [ -d "tests" ]; then
        python -m pytest tests/ -v
        print_success "测试完成"
    else
        print_warning "未找到测试目录"
    fi
}

# 运行示例
run_examples() {
    print_info "运行使用示例..."
    
    if [ -f "examples/usage_examples.py" ]; then
        python examples/usage_examples.py
    else
        print_error "未找到示例文件"
        exit 1
    fi
}

# 健康检查
health_check() {
    print_info "执行健康检查..."
    python main.py health
}

# 显示帮助信息
show_help() {
    echo "Placekey地址标准化工具 - 快速启动脚本"
    echo ""
    echo "使用方法: ./run.sh [command] [options]"
    echo ""
    echo "可用命令:"
    echo "  setup     - 设置项目环境（创建虚拟环境、安装依赖）"
    echo "  test      - 运行测试"
    echo "  examples  - 运行使用示例"
    echo "  health    - 执行API健康检查"
    echo "  single    - 处理单个地址"
    echo "  batch     - 批量处理CSV文件"
    echo "  apartment - 分析地址中的公寓信息"
    echo "  help      - 显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  ./run.sh setup"
    echo "  ./run.sh test"
    echo "  ./run.sh single -a '1543 Mission Street APT 3' -c 'San Francisco' -s 'CA' -z '94105'"
    echo "  ./run.sh batch -i examples/sample_addresses.csv -o output.csv"
    echo "  ./run.sh apartment -a '1543 Mission Street APT 3'"
    echo ""
    echo "环境变量:"
    echo "  PLACEKEY_API_KEY - Placekey API密钥（必需）"
    echo ""
}

# 主函数
main() {
    case "${1:-help}" in
        "setup")
            print_info "开始设置项目环境..."
            check_python
            setup_venv
            install_deps
            check_env
            print_success "项目环境设置完成！"
            print_info "请设置.env文件中的API密钥，然后运行: ./run.sh health"
            ;;
        "test")
            check_python
            if [ -d "venv" ]; then
                source venv/bin/activate
            fi
            run_tests
            ;;
        "examples")
            check_python
            if [ -d "venv" ]; then
                source venv/bin/activate
            fi
            check_env
            run_examples
            ;;
        "health")
            check_python
            if [ -d "venv" ]; then
                source venv/bin/activate
            fi
            check_env
            health_check
            ;;
        "single")
            check_python
            if [ -d "venv" ]; then
                source venv/bin/activate
            fi
            check_env
            shift
            python main.py single "$@"
            ;;
        "batch")
            check_python
            if [ -d "venv" ]; then
                source venv/bin/activate
            fi
            check_env
            shift
            python main.py batch "$@"
            ;;
        "apartment")
            check_python
            if [ -d "venv" ]; then
                source venv/bin/activate
            fi
            shift
            python main.py apartment "$@"
            ;;
        "help")
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"