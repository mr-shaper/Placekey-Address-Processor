#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地址标准化和预处理模块
提供地址清洗、格式化和验证功能
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from . import config as config_module
from .placekey_client import PlacekeyClient

class AddressProcessor:
    """地址处理器类"""
    
    def __init__(self, placekey_client: Optional[PlacekeyClient] = None):
        """
        初始化地址处理器
        
        Args:
            placekey_client: Placekey客户端实例
        """
        self.client = placekey_client or PlacekeyClient()
        self.logger = logging.getLogger(__name__)
        
        # 编译正则表达式
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译常用的正则表达式模式"""
        # 公寓单元模式
        apt_keywords = '|'.join(config_module.APARTMENT_KEYWORDS)
        self.apt_pattern = re.compile(
            rf'\b({apt_keywords})\s*[#\-\s]*([A-Z0-9]+)\b', 
            re.IGNORECASE
        )
        
        # 街道后缀模式
        self.street_suffix_pattern = re.compile(
            r'\b(' + '|'.join(config_module.ADDRESS_STANDARDIZATION['street_suffixes'].keys()) + r')\b',
            re.IGNORECASE
        )
        
        # 方向词模式
        self.directional_pattern = re.compile(
            r'\b(' + '|'.join(config_module.ADDRESS_STANDARDIZATION['directional'].keys()) + r')\b',
            re.IGNORECASE
        )
        
        # 邮编模式（美国5位或5+4位）
        self.zipcode_pattern = re.compile(r'\b(\d{5})(?:-\d{4})?\b')
        
        # 坐标模式
        self.coordinate_pattern = re.compile(
            r'(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)'
        )
        
        # 清理模式
        self.cleanup_patterns = [
            (re.compile(r'\s+'), ' '),  # 多个空格合并为一个
            (re.compile(r'[,\s]+$'), ''),  # 移除末尾的逗号和空格
            (re.compile(r'^[,\s]+'), ''),  # 移除开头的逗号和空格
        ]
    
    def process_address(self, address_data: Dict[str, Any], 
                       standardize: bool = True) -> Dict[str, Any]:
        """
        处理单个地址
        
        Args:
            address_data: 原始地址数据
            standardize: 是否进行标准化处理
            
        Returns:
            处理结果
        """
        try:
            # 1. 预处理和清洗
            cleaned_data = self.clean_address_data(address_data)
            
            # 2. 标准化（如果需要）
            if standardize:
                standardized_data = self.standardize_address(cleaned_data)
            else:
                standardized_data = cleaned_data
            
            # 3. 验证地址完整性
            validation_result = self.validate_address_completeness(standardized_data)
            
            # 4. 调用Placekey API
            placekey_result = self.client.get_placekey(standardized_data)
            
            # 5. 合并结果
            result = {
                'original_address': address_data,
                'cleaned_address': cleaned_data,
                'standardized_address': standardized_data,
                'validation': validation_result,
                'placekey_result': placekey_result
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"地址处理失败: {str(e)}")
            return {
                'original_address': address_data,
                'error': str(e),
                'success': False
            }
    
    def clean_address_data(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        清洗地址数据
        
        Args:
            address_data: 原始地址数据
            
        Returns:
            清洗后的地址数据
        """
        cleaned = {}
        
        for key, value in address_data.items():
            if value is None:
                continue
                
            if isinstance(value, str):
                # 字符串清洗
                cleaned_value = self._clean_string(value)
                if cleaned_value:
                    cleaned[key] = cleaned_value
            elif isinstance(value, (int, float)):
                # 数值类型直接保留
                cleaned[key] = value
            else:
                # 其他类型转为字符串后清洗
                str_value = str(value).strip()
                if str_value:
                    cleaned[key] = str_value
        
        return cleaned
    
    def _clean_string(self, text: str) -> str:
        """
        清洗字符串
        
        Args:
            text: 原始字符串
            
        Returns:
            清洗后的字符串
        """
        if not text:
            return ''
        
        # 转为大写并去除首尾空格
        cleaned = text.upper().strip()
        
        # 应用清理模式
        for pattern, replacement in self.cleanup_patterns:
            cleaned = pattern.sub(replacement, cleaned)
        
        return cleaned
    
    def standardize_address(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化地址
        
        Args:
            address_data: 清洗后的地址数据
            
        Returns:
            标准化后的地址数据
        """
        standardized = address_data.copy()
        
        # 标准化街道地址
        if 'street_address' in standardized:
            standardized['street_address'] = self._standardize_street_address(
                standardized['street_address']
            )
        
        # 标准化州名
        if 'region' in standardized:
            standardized['region'] = self._standardize_state(
                standardized['region']
            )
        
        # 标准化邮编
        if 'postal_code' in standardized:
            standardized['postal_code'] = self._standardize_zipcode(
                standardized['postal_code']
            )
        
        # 确保国家代码
        if 'iso_country_code' not in standardized:
            standardized['iso_country_code'] = 'US'  # 默认美国
        
        return standardized
    
    def _standardize_street_address(self, street_address: str) -> str:
        """
        标准化街道地址
        
        Args:
            street_address: 原始街道地址
            
        Returns:
            标准化后的街道地址
        """
        if not street_address:
            return ''
        
        address = street_address
        
        # 标准化街道后缀
        def replace_suffix(match):
            suffix = match.group(1).upper()
            return config_module.ADDRESS_STANDARDIZATION['street_suffixes'].get(suffix, suffix)
        
        address = self.street_suffix_pattern.sub(replace_suffix, address)
        
        # 标准化方向词
        def replace_directional(match):
            direction = match.group(1).upper()
            return config_module.ADDRESS_STANDARDIZATION['directional'].get(direction, direction)
        
        address = self.directional_pattern.sub(replace_directional, address)
        
        return address.strip()
    
    def _standardize_state(self, state: str) -> str:
        """
        标准化州名
        
        Args:
            state: 原始州名
            
        Returns:
            标准化后的州名（2位缩写）
        """
        if not state:
            return ''
        
        state = state.upper().strip()
        
        # 美国州名映射表（部分常用的）
        state_mapping = {
            'CALIFORNIA': 'CA',
            'NEW YORK': 'NY',
            'TEXAS': 'TX',
            'FLORIDA': 'FL',
            'ILLINOIS': 'IL',
            'PENNSYLVANIA': 'PA',
            'OHIO': 'OH',
            'GEORGIA': 'GA',
            'NORTH CAROLINA': 'NC',
            'MICHIGAN': 'MI'
        }
        
        return state_mapping.get(state, state)
    
    def _standardize_zipcode(self, zipcode: str) -> str:
        """
        标准化邮编
        
        Args:
            zipcode: 原始邮编
            
        Returns:
            标准化后的邮编
        """
        if not zipcode:
            return ''
        
        # 提取5位邮编
        match = self.zipcode_pattern.search(str(zipcode))
        if match:
            return match.group(1)
        
        return str(zipcode).strip()
    
    def extract_apartment_info(self, street_address: str) -> Tuple[str, Optional[str]]:
        """
        从街道地址中提取公寓信息
        
        Args:
            street_address: 街道地址
            
        Returns:
            (主地址, 公寓单元号) 元组
        """
        if not street_address:
            return '', None
        
        # 查找公寓单元模式
        match = self.apt_pattern.search(street_address)
        if match:
            # 提取公寓单元信息
            apt_type = match.group(1).upper()
            apt_number = match.group(2).upper()
            
            # 移除公寓信息，获取主地址
            main_address = street_address[:match.start()].strip()
            
            # 标准化公寓单元格式
            apartment_unit = f"{apt_type} {apt_number}"
            
            return main_address, apartment_unit
        
        return street_address, None
    
    def validate_address_completeness(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证地址完整性
        
        Args:
            address_data: 地址数据
            
        Returns:
            验证结果
        """
        validation = {
            'is_valid': False,
            'completeness_score': 0,
            'missing_fields': [],
            'warnings': [],
            'validation_type': 'unknown'
        }
        
        # 检查坐标信息
        has_coordinates = (
            'latitude' in address_data and 
            'longitude' in address_data and
            address_data['latitude'] is not None and
            address_data['longitude'] is not None
        )
        
        # 检查地址字段
        required_fields = ['street_address', 'city', 'region', 'postal_code']
        present_fields = [field for field in required_fields 
                         if field in address_data and address_data[field]]
        
        if has_coordinates:
            validation['is_valid'] = True
            validation['completeness_score'] = 100
            validation['validation_type'] = 'coordinates'
        elif len(present_fields) >= 3:  # 至少3个地址字段
            validation['is_valid'] = True
            validation['completeness_score'] = (len(present_fields) / len(required_fields)) * 100
            validation['validation_type'] = 'address'
            validation['missing_fields'] = [field for field in required_fields 
                                          if field not in present_fields]
        else:
            validation['missing_fields'] = [field for field in required_fields 
                                          if field not in present_fields]
            validation['completeness_score'] = (len(present_fields) / len(required_fields)) * 100
        
        # 添加警告
        if not has_coordinates and 'street_address' not in present_fields:
            validation['warnings'].append('缺少街道地址，可能影响匹配精度')
        
        if not has_coordinates and 'postal_code' not in present_fields:
            validation['warnings'].append('缺少邮编，可能影响匹配精度')
        
        return validation
    
    def parse_coordinates_from_string(self, coord_string: str) -> Optional[Tuple[float, float]]:
        """
        从字符串中解析坐标
        
        Args:
            coord_string: 坐标字符串
            
        Returns:
            (纬度, 经度) 元组，解析失败返回None
        """
        if not coord_string:
            return None
        
        match = self.coordinate_pattern.search(coord_string)
        if match:
            try:
                lat = float(match.group(1))
                lng = float(match.group(2))
                
                # 验证坐标范围
                if -90 <= lat <= 90 and -180 <= lng <= 180:
                    return lat, lng
            except ValueError:
                pass
        
        return None
    
    def suggest_address_improvements(self, address_data: Dict[str, Any]) -> List[str]:
        """
        建议地址改进方案
        
        Args:
            address_data: 地址数据
            
        Returns:
            改进建议列表
        """
        suggestions = []
        
        # 检查必要字段
        if 'street_address' not in address_data or not address_data['street_address']:
            suggestions.append('添加完整的街道地址')
        
        if 'city' not in address_data or not address_data['city']:
            suggestions.append('添加城市名称')
        
        if 'region' not in address_data or not address_data['region']:
            suggestions.append('添加州/省份信息')
        
        if 'postal_code' not in address_data or not address_data['postal_code']:
            suggestions.append('添加邮编信息')
        
        if 'iso_country_code' not in address_data or not address_data['iso_country_code']:
            suggestions.append('添加国家代码（如US）')
        
        # 检查地址格式
        if 'street_address' in address_data:
            street = address_data['street_address']
            if not re.search(r'\d+', street):
                suggestions.append('街道地址应包含门牌号')
        
        return suggestions