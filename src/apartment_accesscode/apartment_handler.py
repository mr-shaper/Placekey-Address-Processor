#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公寓房号识别和处理模块
专门处理各种公寓单元格式的识别、标准化和聚合逻辑
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from collections import defaultdict
from . import config as config_module

class ApartmentHandler:
    """公寓房号处理器类"""
    
    def __init__(self):
        """
        初始化公寓处理器
        """
        self.logger = logging.getLogger(__name__)
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译公寓识别的正则表达式模式"""
        # 基础公寓关键词模式
        apt_keywords = '|'.join(config_module.APARTMENT_KEYWORDS)
        
        # 标准公寓模式：APT 5, UNIT A, SUITE 100等
        self.standard_apt_pattern = re.compile(
            rf'\b({apt_keywords})\s*[#\-\s]*([A-Z0-9]+)\b',
            re.IGNORECASE
        )
        
        # 简化公寓模式：#5, -A, 3A等
        self.simple_apt_pattern = re.compile(
            r'[#\-]\s*([A-Z0-9]+)(?=\s|$)|\b(\d+[A-Z])\b',
            re.IGNORECASE
        )
        
        # 楼层房间模式：Floor 3 Room 5, 3F-5等
        self.floor_room_pattern = re.compile(
            r'(?:FLOOR|FL|F)\s*(\d+)\s*(?:ROOM|RM|R)?\s*([A-Z0-9]*)|'
            r'(\d+)F[\-\s]*([A-Z0-9]+)',
            re.IGNORECASE
        )
        
        # 复合公寓模式：Building 2 Apt 5, Bldg A Unit 3等
        self.compound_apt_pattern = re.compile(
            rf'(?:BUILDING|BLDG|BLD)\s*([A-Z0-9]+)\s*(?:{apt_keywords})\s*([A-Z0-9]+)|'
            rf'({apt_keywords})\s*([A-Z0-9]+)\s*(?:BUILDING|BLDG|BLD)\s*([A-Z0-9]+)',
            re.IGNORECASE
        )
        
        # 范围模式：Apt 1-5, Unit A-C等
        self.range_pattern = re.compile(
            rf'({apt_keywords})\s*([A-Z0-9]+)\s*[\-~]\s*([A-Z0-9]+)',
            re.IGNORECASE
        )
        
        # 多单元模式：Apt 1&2, Unit A,B,C等
        self.multi_unit_pattern = re.compile(
            rf'({apt_keywords})\s*([A-Z0-9]+(?:[&,\s]+[A-Z0-9]+)+)',
            re.IGNORECASE
        )
    
    def identify_apartment_type(self, street_address: str) -> Dict[str, Any]:
        """
        识别地址中的公寓类型和信息
        
        Args:
            street_address: 街道地址
            
        Returns:
            公寓信息字典
        """
        if not street_address:
            return {
                'has_apartment': False,
                'apartment_type': None,
                'apartment_info': None,
                'main_address': street_address,
                'confidence': 0
            }
        
        address = street_address.upper().strip()
        
        # 按优先级检查不同模式
        patterns = [
            ('compound', self.compound_apt_pattern, self._parse_compound_apartment),
            ('floor_room', self.floor_room_pattern, self._parse_floor_room),
            ('range', self.range_pattern, self._parse_range_apartment),
            ('multi_unit', self.multi_unit_pattern, self._parse_multi_unit),
            ('standard', self.standard_apt_pattern, self._parse_standard_apartment),
            ('simple', self.simple_apt_pattern, self._parse_simple_apartment)
        ]
        
        for pattern_name, pattern, parser in patterns:
            match = pattern.search(address)
            if match:
                try:
                    result = parser(match, address)
                    result['apartment_type'] = pattern_name
                    result['has_apartment'] = True
                    return result
                except Exception as e:
                    self.logger.warning(f"解析{pattern_name}模式失败: {str(e)}")
                    continue
        
        # 没有找到公寓信息
        return {
            'has_apartment': False,
            'apartment_type': None,
            'apartment_info': None,
            'main_address': street_address,
            'confidence': 100  # 确定没有公寓信息
        }
    
    def _parse_standard_apartment(self, match: re.Match, address: str) -> Dict[str, Any]:
        """解析标准公寓模式"""
        apt_type = match.group(1).upper()
        apt_number = match.group(2).upper()
        
        # 获取主地址（移除公寓信息）
        main_address = address[:match.start()].strip()
        
        return {
            'apartment_info': {
                'type': self._standardize_apartment_type(apt_type),
                'number': apt_number,
                'full': f"{self._standardize_apartment_type(apt_type)} {apt_number}"
            },
            'main_address': main_address,
            'confidence': 95
        }
    
    def _parse_simple_apartment(self, match: re.Match, address: str) -> Dict[str, Any]:
        """解析简化公寓模式"""
        apt_number = match.group(1) or match.group(2)
        if apt_number:
            apt_number = apt_number.upper()
            
            # 获取主地址
            main_address = address[:match.start()].strip()
            
            return {
                'apartment_info': {
                    'type': 'UNIT',  # 默认类型
                    'number': apt_number,
                    'full': f"UNIT {apt_number}"
                },
                'main_address': main_address,
                'confidence': 70  # 较低置信度，因为格式不够明确
            }
        
        raise ValueError("无法解析简化公寓格式")
    
    def _parse_floor_room(self, match: re.Match, address: str) -> Dict[str, Any]:
        """解析楼层房间模式"""
        if match.group(1) and match.group(2):  # Floor X Room Y格式
            floor = match.group(1)
            room = match.group(2) or ''
            apt_info = f"FL {floor} RM {room}" if room else f"FL {floor}"
        elif match.group(3) and match.group(4):  # 3F-5格式
            floor = match.group(3)
            room = match.group(4)
            apt_info = f"FL {floor} RM {room}"
        else:
            raise ValueError("无法解析楼层房间格式")
        
        main_address = address[:match.start()].strip()
        
        return {
            'apartment_info': {
                'type': 'FLOOR_ROOM',
                'number': apt_info,
                'full': apt_info,
                'floor': match.group(1) or match.group(3),
                'room': match.group(2) or match.group(4)
            },
            'main_address': main_address,
            'confidence': 85
        }
    
    def _parse_compound_apartment(self, match: re.Match, address: str) -> Dict[str, Any]:
        """解析复合公寓模式"""
        if match.group(1) and match.group(2):  # Building X Apt Y
            building = match.group(1)
            apt_number = match.group(2)
            apt_info = f"BLDG {building} APT {apt_number}"
        elif match.group(3) and match.group(4) and match.group(5):  # Apt X Building Y
            apt_type = match.group(3).upper()
            apt_number = match.group(4)
            building = match.group(5)
            apt_info = f"BLDG {building} {self._standardize_apartment_type(apt_type)} {apt_number}"
        else:
            raise ValueError("无法解析复合公寓格式")
        
        main_address = address[:match.start()].strip()
        
        return {
            'apartment_info': {
                'type': 'COMPOUND',
                'number': apt_info,
                'full': apt_info,
                'building': building if 'building' in locals() else match.group(1)
            },
            'main_address': main_address,
            'confidence': 90
        }
    
    def _parse_range_apartment(self, match: re.Match, address: str) -> Dict[str, Any]:
        """解析范围公寓模式"""
        apt_type = match.group(1).upper()
        start_unit = match.group(2).upper()
        end_unit = match.group(3).upper()
        
        main_address = address[:match.start()].strip()
        
        return {
            'apartment_info': {
                'type': 'RANGE',
                'number': f"{start_unit}-{end_unit}",
                'full': f"{self._standardize_apartment_type(apt_type)} {start_unit}-{end_unit}",
                'range_start': start_unit,
                'range_end': end_unit
            },
            'main_address': main_address,
            'confidence': 80
        }
    
    def _parse_multi_unit(self, match: re.Match, address: str) -> Dict[str, Any]:
        """解析多单元模式"""
        apt_type = match.group(1).upper()
        units_str = match.group(2)
        
        # 解析多个单元号
        units = re.split(r'[&,\s]+', units_str.upper())
        units = [unit.strip() for unit in units if unit.strip()]
        
        main_address = address[:match.start()].strip()
        
        return {
            'apartment_info': {
                'type': 'MULTI_UNIT',
                'number': ','.join(units),
                'full': f"{self._standardize_apartment_type(apt_type)} {','.join(units)}",
                'units': units
            },
            'main_address': main_address,
            'confidence': 85
        }
    
    def _standardize_apartment_type(self, apt_type: str) -> str:
        """标准化公寓类型"""
        apt_type = apt_type.upper().strip()
        
        # 标准化映射
        type_mapping = {
            'APARTMENT': 'APT',
            'UNIT': 'UNIT',
            'SUITE': 'STE',
            'BUILDING': 'BLDG',
            'ROOM': 'RM',
            'FLOOR': 'FL',
            'PENTHOUSE': 'PH'
        }
        
        return type_mapping.get(apt_type, apt_type)
    
    def group_apartments_by_building(self, addresses: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        按建筑物分组公寓地址
        
        Args:
            addresses: 地址列表，每个地址包含apartment_info
            
        Returns:
            按主地址分组的字典
        """
        grouped = defaultdict(list)
        
        for address in addresses:
            if 'apartment_info' in address and address['apartment_info']:
                main_address = address.get('main_address', '')
                if main_address:
                    grouped[main_address].append(address)
                else:
                    # 如果没有主地址，使用完整地址作为键
                    full_address = address.get('street_address', '')
                    grouped[full_address].append(address)
            else:
                # 非公寓地址单独分组
                full_address = address.get('street_address', '')
                grouped[full_address].append(address)
        
        return dict(grouped)
    
    def should_aggregate_apartments(self, apartment_group: List[Dict[str, Any]]) -> bool:
        """
        判断是否应该聚合公寓单元
        
        Args:
            apartment_group: 同一建筑物的公寓列表
            
        Returns:
            是否应该聚合
        """
        if len(apartment_group) <= 1:
            return False
        
        # 检查是否都有相同的主地址
        main_addresses = set()
        for apt in apartment_group:
            main_addr = apt.get('main_address', '')
            if main_addr:
                main_addresses.add(main_addr)
        
        # 如果主地址相同，建议聚合
        return len(main_addresses) == 1
    
    def create_building_summary(self, apartment_group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        创建建筑物汇总信息
        
        Args:
            apartment_group: 同一建筑物的公寓列表
            
        Returns:
            建筑物汇总信息
        """
        if not apartment_group:
            return {}
        
        # 获取主地址
        main_address = apartment_group[0].get('main_address', '')
        
        # 收集所有单元信息
        units = []
        unit_types = set()
        
        for apt in apartment_group:
            apt_info = apt.get('apartment_info', {})
            if apt_info:
                units.append(apt_info.get('number', ''))
                unit_types.add(apt_info.get('type', ''))
        
        return {
            'main_address': main_address,
            'total_units': len(apartment_group),
            'unit_numbers': units,
            'unit_types': list(unit_types),
            'should_get_building_placekey': True,
            'individual_apartments': apartment_group
        }
    
    def extract_apartment_variations(self, street_address: str) -> List[str]:
        """
        提取地址的不同变体（用于匹配相似地址）
        
        Args:
            street_address: 街道地址
            
        Returns:
            地址变体列表
        """
        variations = [street_address]
        
        # 识别公寓信息
        apt_info = self.identify_apartment_type(street_address)
        
        if apt_info['has_apartment']:
            main_address = apt_info['main_address']
            apt_data = apt_info['apartment_info']
            
            # 添加主地址（不含公寓信息）
            if main_address:
                variations.append(main_address)
            
            # 添加不同格式的公寓表示
            if apt_data:
                apt_type = apt_data.get('type', '')
                apt_number = apt_data.get('number', '')
                
                if apt_type and apt_number:
                    # 标准格式
                    variations.append(f"{main_address} {apt_type} {apt_number}")
                    # 简化格式
                    variations.append(f"{main_address} #{apt_number}")
                    # 全称格式
                    if apt_type == 'APT':
                        variations.append(f"{main_address} APARTMENT {apt_number}")
                    elif apt_type == 'STE':
                        variations.append(f"{main_address} SUITE {apt_number}")
        
        # 去重并返回
        return list(set(variations))
    
    def normalize_apartment_format(self, street_address: str, 
                                 target_format: str = 'standard') -> str:
        """
        标准化公寓地址格式
        
        Args:
            street_address: 原始街道地址
            target_format: 目标格式 ('standard', 'short', 'full')
            
        Returns:
            标准化后的地址
        """
        apt_info = self.identify_apartment_type(street_address)
        
        if not apt_info['has_apartment']:
            return street_address
        
        main_address = apt_info['main_address']
        apt_data = apt_info['apartment_info']
        
        if not apt_data:
            return street_address
        
        apt_type = apt_data.get('type', '')
        apt_number = apt_data.get('number', '')
        
        if target_format == 'standard':
            return f"{main_address} {apt_type} {apt_number}"
        elif target_format == 'short':
            return f"{main_address} #{apt_number}"
        elif target_format == 'full':
            type_full_names = {
                'APT': 'APARTMENT',
                'STE': 'SUITE',
                'UNIT': 'UNIT',
                'BLDG': 'BUILDING',
                'RM': 'ROOM',
                'FL': 'FLOOR'
            }
            full_type = type_full_names.get(apt_type, apt_type)
            return f"{main_address} {full_type} {apt_number}"
        
        return street_address
    
    def get_apartment_statistics(self, addresses: List[str]) -> Dict[str, Any]:
        """
        获取地址列表的公寓统计信息
        
        Args:
            addresses: 地址列表
            
        Returns:
            统计信息
        """
        stats = {
            'total_addresses': len(addresses),
            'apartment_addresses': 0,
            'non_apartment_addresses': 0,
            'apartment_types': defaultdict(int),
            'buildings_with_multiple_units': 0,
            'unique_buildings': set()
        }
        
        building_units = defaultdict(list)
        
        for address in addresses:
            apt_info = self.identify_apartment_type(address)
            
            if apt_info['has_apartment']:
                stats['apartment_addresses'] += 1
                
                apt_data = apt_info['apartment_info']
                if apt_data:
                    apt_type = apt_data.get('type', 'unknown')
                    stats['apartment_types'][apt_type] += 1
                
                main_address = apt_info['main_address']
                if main_address:
                    stats['unique_buildings'].add(main_address)
                    building_units[main_address].append(address)
            else:
                stats['non_apartment_addresses'] += 1
        
        # 统计有多个单元的建筑物
        for building, units in building_units.items():
            if len(units) > 1:
                stats['buildings_with_multiple_units'] += 1
        
        stats['unique_buildings'] = len(stats['unique_buildings'])
        stats['apartment_types'] = dict(stats['apartment_types'])
        
        return stats