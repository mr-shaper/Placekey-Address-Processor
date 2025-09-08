#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公寓处理模块测试
"""

import unittest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apartment_handler import ApartmentHandler

class TestApartmentHandler(unittest.TestCase):
    """公寓处理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.handler = ApartmentHandler()
    
    def test_identify_apartment_type_apt(self):
        """测试APT格式识别"""
        address = "1543 Mission Street APT 3"
        result = self.handler.identify_apartment_type(address)
        
        self.assertTrue(result['has_apartment'])
        self.assertEqual(result['apartment_type'], 'APT')
        self.assertEqual(result['main_address'], '1543 Mission Street')
        self.assertIsNotNone(result['apartment_info'])
        self.assertEqual(result['apartment_info']['number'], '3')
    
    def test_identify_apartment_type_unit(self):
        """测试UNIT格式识别"""
        address = "123 Main Street UNIT 101"
        result = self.handler.identify_apartment_type(address)
        
        self.assertTrue(result['has_apartment'])
        self.assertEqual(result['apartment_type'], 'UNIT')
        self.assertEqual(result['main_address'], '123 Main Street')
        self.assertEqual(result['apartment_info']['number'], '101')
    
    def test_identify_apartment_type_suite(self):
        """测试SUITE格式识别"""
        address = "456 Oak Avenue SUITE 200"
        result = self.handler.identify_apartment_type(address)
        
        self.assertTrue(result['has_apartment'])
        self.assertEqual(result['apartment_type'], 'SUITE')
        self.assertEqual(result['main_address'], '456 Oak Avenue')
        self.assertEqual(result['apartment_info']['number'], '200')
    
    def test_identify_apartment_type_hash(self):
        """测试#格式识别"""
        address = "789 Pine Street #2B"
        result = self.handler.identify_apartment_type(address)
        
        self.assertTrue(result['has_apartment'])
        self.assertEqual(result['apartment_type'], 'UNIT')
        self.assertEqual(result['main_address'], '789 Pine Street')
        self.assertEqual(result['apartment_info']['number'], '2B')
    
    def test_identify_apartment_type_building_room(self):
        """测试BUILDING + ROOM格式识别"""
        address = "321 Elm Drive BUILDING 1 RM 509"
        result = self.handler.identify_apartment_type(address)
        
        self.assertTrue(result['has_apartment'])
        self.assertIn(result['apartment_type'], ['BUILDING', 'ROOM'])
        self.assertEqual(result['main_address'], '321 Elm Drive')
    
    def test_identify_apartment_type_no_apartment(self):
        """测试无公寓信息的地址"""
        address = "654 Maple Lane"
        result = self.handler.identify_apartment_type(address)
        
        self.assertFalse(result['has_apartment'])
        self.assertEqual(result['apartment_type'], 'NONE')
        self.assertEqual(result['main_address'], address)
        self.assertIsNone(result['apartment_info'])
    
    def test_normalize_apartment_format_standard(self):
        """测试标准格式标准化"""
        address = "1543 Mission Street APT 3"
        normalized = self.handler.normalize_apartment_format(address, 'standard')
        
        self.assertEqual(normalized, "1543 Mission Street APT 3")
    
    def test_normalize_apartment_format_short(self):
        """测试短格式标准化"""
        address = "1543 Mission Street APARTMENT 3"
        normalized = self.handler.normalize_apartment_format(address, 'short')
        
        self.assertIn('APT', normalized)
    
    def test_extract_apartment_variations(self):
        """测试地址变体提取"""
        address = "1543 Mission Street APT 3"
        variations = self.handler.extract_apartment_variations(address)
        
        self.assertIsInstance(variations, list)
        self.assertGreater(len(variations), 0)
        self.assertIn("1543 Mission Street", variations)  # 主地址应该在变体中
    
    def test_group_by_building(self):
        """测试按建筑物分组"""
        addresses = [
            "1543 Mission Street APT 1",
            "1543 Mission Street APT 3",
            "1543 Mission Street APT 5",
            "123 Main Street SUITE 200",
            "123 Main Street SUITE 201"
        ]
        
        grouped = self.handler.group_by_building(addresses)
        
        self.assertIsInstance(grouped, dict)
        self.assertEqual(len(grouped), 2)  # 应该有2个建筑物
        
        # 检查Mission Street建筑物
        mission_key = None
        for key in grouped.keys():
            if 'Mission Street' in key:
                mission_key = key
                break
        
        self.assertIsNotNone(mission_key)
        self.assertEqual(len(grouped[mission_key]), 3)  # 应该有3个单元
    
    def test_extract_apartment_info_complex(self):
        """测试复杂公寓信息提取"""
        test_cases = [
            ("123 Main St APT 4C", {'type': 'APT', 'number': '4C'}),
            ("456 Oak Ave UNIT 101", {'type': 'UNIT', 'number': '101'}),
            ("789 Pine St #2B", {'type': 'UNIT', 'number': '2B'}),
            ("321 Elm Dr SUITE 200", {'type': 'SUITE', 'number': '200'})
        ]
        
        for address, expected in test_cases:
            with self.subTest(address=address):
                result = self.handler.identify_apartment_type(address)
                
                if result['has_apartment'] and result['apartment_info']:
                    apt_info = result['apartment_info']
                    self.assertEqual(apt_info['number'], expected['number'])
    
    def test_confidence_scoring(self):
        """测试置信度评分"""
        # 高置信度：标准格式
        high_confidence = self.handler.identify_apartment_type("123 Main Street APT 4")
        
        # 低置信度：模糊格式
        low_confidence = self.handler.identify_apartment_type("123 Main Street Floor 2")
        
        if high_confidence['has_apartment']:
            self.assertGreaterEqual(high_confidence['confidence'], 80)
        
        if low_confidence['has_apartment']:
            self.assertLess(low_confidence['confidence'], high_confidence['confidence'])
    
    def test_edge_cases(self):
        """测试边界情况"""
        edge_cases = [
            "",  # 空字符串
            "   ",  # 只有空格
            "123",  # 只有数字
            "APT 3",  # 只有公寓信息
            "123 Main Street APT",  # 缺少公寓号
            "123 Main Street APT ABC DEF"  # 复杂公寓号
        ]
        
        for address in edge_cases:
            with self.subTest(address=repr(address)):
                try:
                    result = self.handler.identify_apartment_type(address)
                    self.assertIsInstance(result, dict)
                    self.assertIn('has_apartment', result)
                    self.assertIn('apartment_type', result)
                    self.assertIn('main_address', result)
                except Exception as e:
                    self.fail(f"处理地址 {repr(address)} 时出错: {str(e)}")

if __name__ == '__main__':
    unittest.main()