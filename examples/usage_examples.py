#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用示例脚本
展示如何使用Placekey地址标准化工具的各个功能
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import config
from src.placekey_client import PlacekeyClient, PlacekeyAPIError
from src.address_processor import AddressProcessor
from src.apartment_handler import ApartmentHandler
from src.batch_processor import BatchProcessor

def example_single_address():
    """示例1: 处理单个地址"""
    print("\n=== 示例1: 处理单个地址 ===")
    
    try:
        # 初始化处理器
        processor = AddressProcessor()
        
        # 准备地址数据
        address_data = {
            'street_address': '1543 Mission Street APT 3',
            'city': 'San Francisco',
            'region': 'CA',
            'postal_code': '94105',
            'iso_country_code': 'US'
        }
        
        print(f"输入地址: {address_data['street_address']}")
        print(f"城市: {address_data['city']}, {address_data['region']} {address_data['postal_code']}")
        
        # 处理地址
        result = processor.process_address(address_data)
        
        # 显示结果
        if result['placekey_result']['success']:
            print(f"✅ Placekey: {result['placekey_result']['placekey']}")
            print(f"置信度: {result['placekey_result'].get('confidence', 'unknown')}")
        else:
            print(f"❌ 处理失败: {result['placekey_result']['error']}")
            
    except Exception as e:
        print(f"示例1执行失败: {str(e)}")

def example_apartment_analysis():
    """示例2: 公寓信息分析"""
    print("\n=== 示例2: 公寓信息分析 ===")
    
    try:
        # 初始化公寓处理器
        apartment_handler = ApartmentHandler()
        
        # 测试不同格式的地址
        test_addresses = [
            "1543 Mission Street APT 3",
            "123 Main Street UNIT 101",
            "456 Oak Avenue #2B",
            "789 Pine Street Suite 200",
            "321 Elm Drive BUILDING 1 RM 509",
            "654 Maple Lane"  # 无公寓信息
        ]
        
        for address in test_addresses:
            print(f"\n分析地址: {address}")
            
            # 识别公寓信息
            apartment_info = apartment_handler.identify_apartment_type(address)
            
            if apartment_info['has_apartment']:
                print(f"  ✅ 包含公寓信息")
                print(f"  类型: {apartment_info['apartment_type']}")
                print(f"  主地址: {apartment_info['main_address']}")
                print(f"  置信度: {apartment_info['confidence']}%")
                
                apt_data = apartment_info['apartment_info']
                if apt_data:
                    print(f"  单元: {apt_data['full']}")
            else:
                print(f"  ❌ 无公寓信息")
            
            # 显示标准化格式
            normalized = apartment_handler.normalize_apartment_format(address, 'standard')
            print(f"  标准化: {normalized}")
            
    except Exception as e:
        print(f"示例2执行失败: {str(e)}")

def example_address_variations():
    """示例3: 地址变体生成"""
    print("\n=== 示例3: 地址变体生成 ===")
    
    try:
        apartment_handler = ApartmentHandler()
        
        address = "1543 Mission Street APT 3"
        print(f"原始地址: {address}")
        
        # 生成地址变体
        variations = apartment_handler.extract_apartment_variations(address)
        
        print("地址变体:")
        for i, variation in enumerate(variations, 1):
            print(f"  {i}. {variation}")
        
        # 显示不同标准化格式
        formats = ['standard', 'short', 'full']
        print("\n标准化格式:")
        for fmt in formats:
            normalized = apartment_handler.normalize_apartment_format(address, fmt)
            print(f"  {fmt.capitalize()}: {normalized}")
            
    except Exception as e:
        print(f"示例3执行失败: {str(e)}")

def example_batch_processing():
    """示例4: 批量处理（模拟）"""
    print("\n=== 示例4: 批量处理（模拟） ===")
    
    try:
        # 创建模拟数据
        sample_data = [
            {
                'street_address': '1543 Mission Street',
                'city': 'San Francisco',
                'region': 'CA',
                'postal_code': '94105',
                'iso_country_code': 'US'
            },
            {
                'street_address': '1543 Mission Street APT 1',
                'city': 'San Francisco',
                'region': 'CA',
                'postal_code': '94105',
                'iso_country_code': 'US'
            },
            {
                'street_address': '1543 Mission Street APT 3',
                'city': 'San Francisco',
                'region': 'CA',
                'postal_code': '94105',
                'iso_country_code': 'US'
            }
        ]
        
        print(f"模拟处理 {len(sample_data)} 条地址记录")
        
        # 初始化处理器
        processor = AddressProcessor()
        apartment_handler = ApartmentHandler()
        
        results = []
        apartment_count = 0
        
        for i, address_data in enumerate(sample_data, 1):
            print(f"\n处理记录 {i}: {address_data['street_address']}")
            
            try:
                # 处理地址
                result = processor.process_address(address_data)
                
                # 分析公寓信息
                apartment_info = apartment_handler.identify_apartment_type(
                    address_data['street_address']
                )
                
                if apartment_info['has_apartment']:
                    apartment_count += 1
                
                # 合并结果
                combined_result = {
                    'input': address_data,
                    'placekey_result': result['placekey_result'],
                    'apartment_info': apartment_info
                }
                
                results.append(combined_result)
                
                if result['placekey_result']['success']:
                    print(f"  ✅ Placekey: {result['placekey_result']['placekey']}")
                else:
                    print(f"  ❌ 失败: {result['placekey_result']['error']}")
                    
            except Exception as e:
                print(f"  ❌ 处理失败: {str(e)}")
        
        # 显示统计信息
        print(f"\n=== 处理统计 ===")
        print(f"总记录数: {len(sample_data)}")
        print(f"成功处理: {len(results)}")
        print(f"公寓地址: {apartment_count}")
        print(f"非公寓地址: {len(results) - apartment_count}")
        
    except Exception as e:
        print(f"示例4执行失败: {str(e)}")

def example_apartment_aggregation():
    """示例5: 公寓聚合"""
    print("\n=== 示例5: 公寓聚合 ===")
    
    try:
        apartment_handler = ApartmentHandler()
        
        # 模拟同一建筑物的不同单元
        addresses = [
            "1543 Mission Street APT 1",
            "1543 Mission Street APT 3",
            "1543 Mission Street APT 5",
            "1543 Mission Street UNIT 101",
            "123 Main Street SUITE 200",
            "123 Main Street SUITE 201"
        ]
        
        print("原始地址列表:")
        for i, addr in enumerate(addresses, 1):
            print(f"  {i}. {addr}")
        
        # 按建筑物分组
        grouped = apartment_handler.group_by_building(addresses)
        
        print(f"\n聚合结果 ({len(grouped)} 个建筑物):")
        for building, units in grouped.items():
            print(f"\n建筑物: {building}")
            print(f"单元数量: {len(units)}")
            print("单元列表:")
            for unit in units:
                print(f"  - {unit}")
        
    except Exception as e:
        print(f"示例5执行失败: {str(e)}")

def example_api_health_check():
    """示例6: API健康检查"""
    print("\n=== 示例6: API健康检查 ===")
    
    try:
        # 检查配置
        validation = config.validate_config()
        print(f"配置状态: {'✅ 有效' if validation['valid'] else '❌ 无效'}")
        
        if not validation['valid']:
            print("配置问题:")
            for issue in validation['issues']:
                print(f"  - {issue}")
            return
        
        # 检查API连接
        client = PlacekeyClient()
        print("正在检查API连接...")
        
        is_healthy = client.health_check()
        
        if is_healthy:
            print("✅ API连接正常")
        else:
            print("❌ API连接失败")
            
    except Exception as e:
        print(f"示例6执行失败: {str(e)}")

def main():
    """运行所有示例"""
    print("Placekey地址标准化工具 - 使用示例")
    print("=" * 50)
    
    # 检查环境变量
    if not os.getenv('PLACEKEY_API_KEY'):
        print("⚠️  警告: 未设置PLACEKEY_API_KEY环境变量")
        print("请先设置API密钥: export PLACEKEY_API_KEY='your_api_key'")
        print("或创建.env文件并添加: PLACEKEY_API_KEY=your_api_key")
        print("\n继续运行示例（部分功能可能无法正常工作）...")
    
    try:
        # 运行所有示例
        example_api_health_check()
        example_apartment_analysis()
        example_address_variations()
        example_apartment_aggregation()
        
        # 只有在API可用时才运行需要API的示例
        if os.getenv('PLACEKEY_API_KEY'):
            example_single_address()
            example_batch_processing()
        else:
            print("\n⚠️  跳过需要API密钥的示例")
        
        print("\n=== 所有示例执行完成 ===")
        print("\n使用说明:")
        print("1. 设置API密钥后可使用完整功能")
        print("2. 使用命令行工具: python main.py --help")
        print("3. 批量处理CSV文件: python main.py batch -i input.csv -o output.csv")
        print("4. 处理单个地址: python main.py single -a '1543 Mission Street APT 3' -c 'San Francisco' -s 'CA' -z '94105'")
        
    except KeyboardInterrupt:
        print("\n用户中断执行")
    except Exception as e:
        print(f"\n执行失败: {str(e)}")

if __name__ == '__main__':
    main()