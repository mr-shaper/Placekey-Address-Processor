#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试反向映射改进效果
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from placekey_reverse_mapper import CompletePlacekeyMapper

def test_reverse_mapping():
    """测试反向映射功能"""
    
    # 初始化反向映射器
    mapper = CompletePlacekeyMapper(geocoding_service="nominatim")
    
    # 测试第一行数据的坐标（问题案例）
    test_coordinates = [
        (34.0451172788492, -117.288839907418, "Colton, CA - 2270 Cahuilla St Apt 154"),
        (32.75624, -117.10032, "San Diego, CA - 4340 44th St Apt 529"),
        (38.508960273229, -121.433075174561, "Sacramento, CA - 6100 48th Ave Apt 5208")
    ]
    
    print("=" * 80)
    print("测试反向映射改进效果")
    print("=" * 80)
    
    for i, (lat, lng, description) in enumerate(test_coordinates, 1):
        print(f"\n测试 {i}: {description}")
        print(f"坐标: ({lat}, {lng})")
        print("-" * 60)
        
        # 执行反向映射
        result = mapper._reverse_geocode_nominatim(lat, lng)
        
        if result:
            print(f"反向映射结果: {result}")
            
            # 检查是否包含街道信息
            has_street = any([
                'street' in result.lower(),
                'avenue' in result.lower(), 
                'boulevard' in result.lower(),
                'drive' in result.lower(),
                'lane' in result.lower(),
                'way' in result.lower(),
                any(char.isdigit() for char in result.split(',')[0])  # 检查第一部分是否包含数字（门牌号）
            ])
            
            if has_street:
                print("✅ 包含街道地址信息")
            else:
                print("⚠️  只包含城市级别信息")
        else:
            print("❌ 反向映射失败")
        
        print("-" * 60)

if __name__ == "__main__":
    test_reverse_mapping()