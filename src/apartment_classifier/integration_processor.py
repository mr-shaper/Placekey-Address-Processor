#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整合处理器 - 结合现有公寓识别规则与Placekey API
处理用户现有数据格式并提供增强的地址标准化功能
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import logging
from datetime import datetime

from . import config as config_module
from .placekey_client import PlacekeyClient, PlacekeyAPIError
from .address_processor import AddressProcessor
from .apartment_handler import ApartmentHandler

# 导入Placekey反向映射功能
try:
    import sys
    import os
    # 添加项目根目录到Python路径
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from placekey_reverse_mapper import CompletePlacekeyMapper
except ImportError as e:
    CompletePlacekeyMapper = None
    print(f"Warning: Could not import CompletePlacekeyMapper: {e}")

class ExistingApartmentClassifier:
    """现有公寓识别规则实现"""
    
    def __init__(self):
        """初始化分类器"""
        self.logger = logging.getLogger(__name__)
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        # 高置信度关键词 (90%)
        self.high_confidence_keywords = [
            'apartment', 'apt', 'unit', 'suite', 'ste',
            'penthouse', 'ph', 'studio', 'loft', 'basement', 'bsmt',
            'floor', 'fl', 'level', 'lvl'
        ]
        
        # 中等置信度关键词 (75%)
        self.medium_confidence_keywords = [
            'building', 'bldg', 'room', 'rm',
            'department', 'dept', 'office', 'ofc',
            'condo', 'condominium'
        ]
        
        # 低置信度关键词 (55%)
        self.low_confidence_keywords = [
            'trailer', 'trlr', 'lobby', 'lbby',
            'north', 'south', 'east', 'west',
            'upper', 'lower', 'side', 'left', 'right', 'front', 'rear',
            'pier', 'slip', 'space', 'key', 'lot'
        ]
        
        # 需要验证关键词 (35%)
        self.verification_keywords = ['box', 'mailbox', 'pmb']
        
        # 排除关键词
        self.exclude_keywords = ['townhouse', 'th', 'duplex', 'stop', 'hanger']
        
        # 街道类型词汇
        self.street_types = [
            'street', 'st', 'avenue', 'ave', 'road', 'rd', 'lane', 'ln',
            'drive', 'dr', 'court', 'ct', 'circle', 'cir', 'boulevard', 'blvd',
            'place', 'pl', 'way', 'terrace', 'ter', 'parkway', 'pkwy',
            'highway', 'hwy', 'freeway', 'fwy', 'expressway', 'expy',
            'plaza', 'square', 'sq', 'park', 'point', 'pt', 'ridge',
            'hill', 'heights', 'hts', 'valley', 'view', 'lake', 'river',
            'broadway', 'main', 'first', 'second', 'third', 'fourth', 'fifth'
        ]
        
        # 编译正则表达式
        self.number_pattern = re.compile(r'\b(?:no|num|number)\s+\d+\b', re.IGNORECASE)
        self.hash_pattern = re.compile(r'#\s*\d+', re.IGNORECASE)
        self.street_pattern = re.compile(
            r'\b(?:' + '|'.join(self.street_types) + r')\b', 
            re.IGNORECASE
        )
    
    def extract_street_address(self, full_address: str) -> str:
        """从完整地址中提取街道地址部分"""
        if not full_address or not isinstance(full_address, str):
            return ""
        
        # 按照用户格式: 州~~~县~~~城市~~~街道地址
        parts = full_address.split('~~~')
        if len(parts) >= 4:
            return parts[-1].strip()
        else:
            # 如果格式不符合，直接返回原地址
            return full_address.strip()
    
    def check_context_exclusion(self, address: str, keyword: str, keyword_pos: int) -> bool:
        """检查上下文排除规则 - 基于参考文件的精确实现"""
        # 上下文相关的词汇
        context_keywords = ['north', 'south', 'east', 'west', 'upper', 'lower', 
                           'side', 'left', 'right', 'front', 'rear', 
                           'pier', 'slip', 'space', 'key', 'lot']
        
        if keyword.lower() not in context_keywords:
            return False
        
        try:
            # 查找关键词在地址中的位置
            keyword_pattern = r'\b' + re.escape(keyword) + r'\b'
            keyword_match = re.search(keyword_pattern, address, re.IGNORECASE)
            
            if not keyword_match:
                return False
            
            keyword_end = keyword_match.end()
            
            # 检查关键词后面是否紧跟街道类型（允许有少量空格或标点）
            remaining_text = address[keyword_end:].strip()
            if remaining_text:
                street_match = re.match(self.street_pattern, remaining_text, re.IGNORECASE)
                if street_match:
                    # 这是街道名称的一部分，比如 "Main St North"
                    return True
            
            # 检查关键词前面是否有街道类型（处理 "North Main St" 这种格式）
            preceding_text = address[:keyword_match.start()].strip()
            if preceding_text:
                # 检查前面的词是否包含街道类型
                street_before_pattern = self.street_pattern.pattern[:-2] + r'\s*$'  # 移除\b，添加行尾
                street_before_match = re.search(street_before_pattern, preceding_text, re.IGNORECASE)
                if street_before_match:
                    return True
            
            return False  # 不需要排除
            
        except Exception as e:
            self.logger.warning(f"上下文检查失败: {str(e)}")
            return False  # 保守处理，不排除
    
    def classify_apartment(self, full_address: str) -> Tuple[bool, int, str]:
        """分类地址是否为公寓
        
        Returns:
            Tuple[bool, int, str]: (是否公寓, 置信度, 匹配关键词)
        """
        if not full_address or not isinstance(full_address, str):
            return False, 0, ""
        
        # 提取街道地址
        street_address = self.extract_street_address(full_address)
        if not street_address:
            return False, 0, ""
        
        address_lower = street_address.lower()
        max_confidence = 0
        matched_keywords = []
        
        # 检查排除关键词
        for keyword in self.exclude_keywords:
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            if pattern.search(address_lower):
                return False, 0, f"excluded({keyword})"
        
        # 检查高置信度关键词 (90%)
        for keyword in self.high_confidence_keywords:
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            match = pattern.search(street_address)
            if match:
                max_confidence = max(max_confidence, 90)
                matched_keywords.append(f"{keyword}({match.group()})")
        
        # 检查中等置信度关键词 (75%)
        for keyword in self.medium_confidence_keywords:
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            match = pattern.search(street_address)
            if match:
                max_confidence = max(max_confidence, 75)
                matched_keywords.append(f"{keyword}({match.group()})")
        
        # 检查编号模式 (75%)
        number_match = self.number_pattern.search(street_address)
        if number_match:
            max_confidence = max(max_confidence, 75)
            matched_keywords.append(f"number({number_match.group()})")
        
        # 检查#号模式 (60%)
        hash_match = self.hash_pattern.search(street_address)
        if hash_match:
            max_confidence = max(max_confidence, 60)
            matched_keywords.append(f"#number({hash_match.group()})")
        
        # 检查低置信度关键词 (55%) - 需要上下文验证
        for keyword in self.low_confidence_keywords:
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            match = pattern.search(street_address)
            if match:
                # 检查上下文排除
                if not self.check_context_exclusion(street_address, keyword, match.start()):
                    max_confidence = max(max_confidence, 55)
                    matched_keywords.append(f"{keyword}({match.group()})")
        
        # 检查需要验证关键词 (35%)
        for keyword in self.verification_keywords:
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            match = pattern.search(street_address)
            if match:
                max_confidence = max(max_confidence, 35)
                matched_keywords.append(f"{keyword}({match.group()})")
        
        # 判断结果
        is_apartment = max_confidence >= 50
        matched_keywords_str = ", ".join(matched_keywords) if matched_keywords else ""
        
        return is_apartment, max_confidence, matched_keywords_str

class IntegrationProcessor:
    """整合处理器 - 结合现有规则与Placekey API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化处理器
        
        Args:
            api_key: Placekey API密钥，如果不提供则从配置中获取
        """
        self.logger = logging.getLogger(__name__)
        
        # 初始化各个组件
        self.existing_classifier = ExistingApartmentClassifier()
        # 如果提供了API密钥，创建专用的PlacekeyClient
        if api_key:
            placekey_client = PlacekeyClient(api_key)
            self.placekey_processor = AddressProcessor(placekey_client)
        else:
            self.placekey_processor = AddressProcessor()
        self.apartment_handler = ApartmentHandler()
        
        # 初始化Placekey反向映射器
        self.reverse_mapper = None
        if CompletePlacekeyMapper:
            try:
                self.reverse_mapper = CompletePlacekeyMapper(api_key=api_key)
                if api_key:
                    self.logger.info("Placekey反向映射器初始化成功（使用API密钥）")
                else:
                    self.logger.info("Placekey反向映射器初始化成功（模拟模式）")
            except Exception as e:
                self.logger.warning(f"Placekey反向映射器初始化失败: {e}")
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'existing_matches': 0,
            'placekey_matches': 0,
            'both_matches': 0,
            'conflicts': 0,
            'api_errors': 0,
            'reverse_mapping_success': 0,
            'reverse_mapping_errors': 0
        }
    
    def parse_user_data_format(self, address_line: str) -> Dict[str, str]:
        """解析用户数据格式
        
        输入格式示例: California~~~San Bernardino~~~Colton~~~2270 Cahuilla St Apt 154
        """
        if not address_line or not isinstance(address_line, str):
            return {}
        
        parts = address_line.split('~~~')
        if len(parts) >= 4:
            return {
                'state': parts[0].strip(),
                'county': parts[1].strip(),
                'city': parts[2].strip(),
                'street_address': parts[3].strip(),
                'full_address': address_line
            }
        else:
            # 如果格式不符合，尝试直接处理
            return {
                'street_address': address_line.strip(),
                'full_address': address_line
            }
    
    def process_single_address(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个地址记录
        
        Args:
            address_data: 包含地址信息的字典
            
        Returns:
            增强后的地址信息字典
        """
        result = address_data.copy()
        self.stats['total_processed'] += 1
        
        try:
            # 解析地址格式 - 支持多种字段名
            full_address = address_data.get('地址', '') or address_data.get('street_address', '') or address_data.get('address', '')
            
            # 如果没有找到地址字段，尝试从其他可能的字段组合
            if not full_address:
                # 尝试组合字段
                street = address_data.get('street_address', '')
                city = address_data.get('city', '')
                region = address_data.get('region', '')
                if street:
                    full_address = street
                elif city and region:
                    full_address = f"{city}, {region}"
            
            parsed_address = self.parse_user_data_format(full_address)
            
            if not parsed_address:
                return self._add_error_result(result, "地址格式解析失败")
            
            # 1. 检查输入数据中是否已有公寓识别结果
            input_is_apt = address_data.get('是否公寓_原规则')
            input_confidence = address_data.get('置信度_原规则')
            input_keywords = address_data.get('匹配关键词_原规则', '')
            
            # 2. 使用现有规则进行分类
            rule_is_apt, rule_confidence, rule_keywords = \
                self.existing_classifier.classify_apartment(full_address)
            
            # 3. 参考原有输入逻辑，按最大化原则选择结果
            maximization_result = self._apply_maximization_principle(
                input_is_apt, input_confidence, input_keywords,
                rule_is_apt, rule_confidence, rule_keywords
            )
            
            # 调试：检查返回值类型
            if not isinstance(maximization_result, tuple) or len(maximization_result) != 3:
                self.logger.error(f"_apply_maximization_principle返回值异常: {type(maximization_result)}, {maximization_result}")
                return self._add_error_result(result, f"最大化原则处理失败: 返回值类型错误")
            
            try:
                existing_is_apt, existing_confidence, existing_keywords = maximization_result
                # 确保类型正确
                existing_is_apt = bool(existing_is_apt)
                existing_confidence = int(existing_confidence) if existing_confidence is not None else 0
                existing_keywords = str(existing_keywords) if existing_keywords is not None else ''
            except (ValueError, TypeError) as e:
                self.logger.error(f"maximization_result解包失败: {e}")
                return self._add_error_result(result, f"最大化原则结果解包失败: {str(e)}")
            
            # 4. 使用Placekey增强处理（仅对确认的公寓地址）
            placekey_result = None
            placekey_apartment_info = None
            
            # 只有当最大化原则确认为公寓时，才调用Placekey API
            should_call_placekey = existing_is_apt and existing_confidence >= 50
            
            try:
                if should_call_placekey:
                    # 构建Placekey API请求数据
                    placekey_data = {
                        'street_address': parsed_address.get('street_address', ''),
                        'city': address_data.get('收件人城市', parsed_address.get('city', '')),
                        'region': address_data.get('收件人省/州', parsed_address.get('state', '')),
                        'postal_code': address_data.get('收件人邮编', ''),
                        'iso_country_code': 'US' if address_data.get('收件人国家', '') == 'United States' else 'US'
                    }
                    
                    # 调用Placekey API
                    placekey_response = self.placekey_processor.process_address(placekey_data)
                    # 从AddressProcessor的响应中提取placekey_result
                    if placekey_response and isinstance(placekey_response, dict):
                        placekey_result = placekey_response.get('placekey_result')
                    else:
                        self.logger.error(f"placekey_response类型错误: {type(placekey_response)}, {placekey_response}")
                        placekey_result = None
                    self.logger.info(f"Placekey API调用结果: {placekey_result}")
                else:
                    # 跳过Placekey API调用，记录原因
                    self.logger.info(f"跳过Placekey API调用 - 不是公寓地址或置信度过低: {existing_is_apt}, {existing_confidence}")
                
                # 使用新的公寓处理器分析
                placekey_apartment_info = self.apartment_handler.identify_apartment_type(
                    parsed_address.get('street_address', '')
                )
                
            except PlacekeyAPIError as e:
                self.logger.warning(f"Placekey API调用失败: {str(e)}")
                self.stats['api_errors'] += 1
            except Exception as e:
                self.logger.error(f"Placekey处理失败: {str(e)}")
                self.stats['api_errors'] += 1
            
            # 3. 整合结果
            try:
                # 调试：检查传入参数的类型
                print(f"[DEBUG] existing_is_apt类型: {type(existing_is_apt)}, 值: {existing_is_apt}")
                print(f"[DEBUG] existing_confidence类型: {type(existing_confidence)}, 值: {existing_confidence}")
                print(f"[DEBUG] existing_keywords类型: {type(existing_keywords)}, 值: {existing_keywords}")
                print(f"[DEBUG] placekey_result类型: {type(placekey_result)}, 值: {placekey_result}")
                print(f"[DEBUG] placekey_apartment_info类型: {type(placekey_apartment_info)}, 值: {placekey_apartment_info}")
                
                # 特别检查是否有tuple类型的变量
                if isinstance(existing_is_apt, tuple):
                    print(f"[ERROR] existing_is_apt是tuple: {existing_is_apt}")
                if isinstance(existing_confidence, tuple):
                    print(f"[ERROR] existing_confidence是tuple: {existing_confidence}")
                if isinstance(existing_keywords, tuple):
                    print(f"[ERROR] existing_keywords是tuple: {existing_keywords}")
                if isinstance(placekey_result, tuple):
                    print(f"[ERROR] placekey_result是tuple: {placekey_result}")
                if isinstance(placekey_apartment_info, tuple):
                    print(f"[ERROR] placekey_apartment_info是tuple: {placekey_apartment_info}")
                
                integrated_result = self._integrate_results(
                    existing_is_apt, existing_confidence, existing_keywords,
                    placekey_result, placekey_apartment_info
                )
                
                # 严格的integrated_result类型和内容检查
                self.logger.debug(f"integrated_result类型: {type(integrated_result)}, 值: {integrated_result}")
                
                # 强制确保integrated_result是字典类型
                if not isinstance(integrated_result, dict):
                    self.logger.warning(f"integrated_result不是字典，类型: {type(integrated_result)}, 值: {integrated_result}")
                    
                    # 如果是tuple，尝试转换
                    if isinstance(integrated_result, tuple) and len(integrated_result) >= 5:
                        integrated_result = {
                            'is_apartment': bool(integrated_result[0]),
                            'confidence': int(integrated_result[1]) if integrated_result[1] is not None else 0,
                            'keywords': str(integrated_result[2]) if integrated_result[2] is not None else '',
                            'status': str(integrated_result[3]) if integrated_result[3] is not None else 'unknown',
                            'conflict': bool(integrated_result[4]) if len(integrated_result) > 4 else False
                        }
                    else:
                        # 使用安全的默认值
                        integrated_result = {
                            'is_apartment': existing_is_apt,
                            'confidence': existing_confidence,
                            'keywords': existing_keywords,
                            'status': 'error',
                            'conflict': False
                        }
                
                # 确保包含所有必需的键
                required_keys = ['is_apartment', 'confidence', 'keywords', 'status', 'conflict']
                for key in required_keys:
                    if key not in integrated_result:
                        self.logger.warning(f"integrated_result缺少键{key}，使用默认值")
                        if key == 'is_apartment':
                            integrated_result[key] = existing_is_apt
                        elif key == 'confidence':
                            integrated_result[key] = existing_confidence
                        elif key == 'keywords':
                            integrated_result[key] = existing_keywords
                        elif key == 'status':
                            integrated_result[key] = 'partial'
                        elif key == 'conflict':
                            integrated_result[key] = False
                            
            except Exception as e:
                self.logger.error(f"整合结果处理失败: {str(e)}")
                integrated_result = {
                    'is_apartment': existing_is_apt,
                    'confidence': existing_confidence,
                    'keywords': existing_keywords,
                    'status': 'error',
                    'conflict': False
                }
            
            # 4. 更新统计
            self._update_stats(existing_is_apt, placekey_apartment_info)
            
            # 5. 提取unit number信息
            unit_number = self._extract_unit_number(placekey_apartment_info, existing_keywords)
            
            # 6. 执行Placekey反向映射（如果有Placekey）
            reverse_mapping_result = self._perform_reverse_mapping(placekey_result)
            
            # 7. 生成标准化地址（用于access code统一）
            standardized_address = self._generate_standardized_address(placekey_result, parsed_address)
            
            # 8. 添加增强信息到结果
            # 调试：检查integrated_result在update前的状态
            if not isinstance(integrated_result, dict):
                self.logger.error(f"准备update时integrated_result类型错误: {type(integrated_result)}, {integrated_result}")
                return self._add_error_result(result, f"结果更新失败: integrated_result不是字典")
            
            result.update({
                # 保留原有字段
                '是否公寓_原规则': existing_is_apt,
                '置信度_原规则': existing_confidence,
                '匹配关键词_原规则': existing_keywords,
                
                # Placekey API返回的所有字段 - 完整字段集
                'placekey': self._safe_get(placekey_result, 'placekey', ''),
                'placekey_confidence': self._safe_get(placekey_result, 'confidence', ''),
                'placekey_matched_address': str(self._safe_get(placekey_result, 'matched_address', '')),
                'placekey_success': bool(self._safe_get(placekey_result, 'success', False)),
                'placekey_error': self._safe_get(placekey_result, 'error', ''),
                'placekey_latitude': self._safe_get(placekey_result, 'latitude', ''),
                'placekey_longitude': self._safe_get(placekey_result, 'longitude', ''),
                'placekey_location_type': self._safe_get(placekey_result, 'location_type', ''),
                'placekey_address_components': str(self._safe_get(placekey_result, 'address_components', {})),
                
                # 单独提取重要的Placekey字段 - 添加更严格的类型检查
                'address_placekey': self._safe_get_nested(placekey_result, ['address_components', 'address_placekey'], ''),
                'building_placekey': self._safe_get_nested(placekey_result, ['address_components', 'building_placekey'], ''),
                'geocode': self._build_geocode_string(placekey_result),
                'confidence': self._safe_get(placekey_result, 'confidence', ''),
                
                # 新增公寓分析字段
                '公寓类型_增强': self._safe_get(placekey_apartment_info, 'apartment_type', 'NONE'),
                '主地址_增强': self._safe_get(placekey_apartment_info, 'main_address', ''),
                '公寓信息_增强': str(self._safe_get(placekey_apartment_info, 'apartment_info', {})),
                
                # 地址标准化字段
                'standardized_address': standardized_address,
                
                # 直接的access code字段
                'access_code': unit_number,
                
                # Placekey反向映射结果
                'reverse_mapping_success': reverse_mapping_result.get('success', False) if reverse_mapping_result else False,
                'reverse_mapping_address': reverse_mapping_result.get('address', '') if reverse_mapping_result else '',
                'reverse_mapping_coordinates': str(reverse_mapping_result.get('coordinates', {})) if reverse_mapping_result else '',
                'reverse_mapping_latitude': reverse_mapping_result.get('coordinates')[0] if reverse_mapping_result and reverse_mapping_result.get('coordinates') and isinstance(reverse_mapping_result.get('coordinates'), tuple) else '',
                'reverse_mapping_longitude': reverse_mapping_result.get('coordinates')[1] if reverse_mapping_result and reverse_mapping_result.get('coordinates') and isinstance(reverse_mapping_result.get('coordinates'), tuple) else '',
                'reverse_mapping_error': reverse_mapping_result.get('error', '') if reverse_mapping_result else '',
                
                # 整合后的最终结果 - 确保安全访问
                '是否公寓_整合': integrated_result.get('is_apartment', False),
                '置信度_整合': integrated_result.get('confidence', 0),
                '匹配关键词_整合': integrated_result.get('keywords', ''),
                '处理状态': integrated_result.get('status', 'error'),
                '冲突标记': integrated_result.get('conflict', False)
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"处理地址失败: {str(e)}")
            return self._add_error_result(result, f"处理失败: {str(e)}")
    
    def _perform_reverse_mapping(self, placekey_result: Optional[Dict]) -> Optional[Dict]:
        """
        执行Placekey反向映射
        
        Args:
            placekey_result: Placekey API返回的结果
            
        Returns:
            反向映射结果字典，包含address、coordinates等信息
        """
        if not self.reverse_mapper or not placekey_result:
            return None
            
        try:
            # 获取Placekey
            placekey = placekey_result.get('placekey')
            if not placekey:
                return {'success': False, 'error': 'No placekey available'}
            
            # 获取Placekey API返回的真实坐标
            existing_coordinates = None
            if 'latitude' in placekey_result and 'longitude' in placekey_result:
                try:
                    lat = float(placekey_result['latitude'])
                    lng = float(placekey_result['longitude'])
                    existing_coordinates = (lat, lng)
                    self.logger.debug(f"使用Placekey API坐标: ({lat}, {lng})")
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"无法解析Placekey API坐标: {e}")
            
            # 执行反向映射，传递真实坐标
            self.logger.debug(f"执行Placekey反向映射: {placekey}")
            mapping_result = self.reverse_mapper.placekey_to_address(placekey, existing_coordinates)
            
            if mapping_result and mapping_result.get('success'):
                self.stats['reverse_mapping_success'] += 1
                self.logger.debug(f"反向映射成功: {mapping_result.get('address', '')}")
                return mapping_result
            else:
                self.stats['reverse_mapping_errors'] += 1
                error_msg = mapping_result.get('error', 'Unknown error') if mapping_result else 'No result returned'
                self.logger.warning(f"反向映射失败: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            self.stats['reverse_mapping_errors'] += 1
            self.logger.error(f"反向映射异常: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _extract_unit_number(self, placekey_apartment_info: Optional[Dict], existing_keywords: str) -> str:
        """
        提取unit number信息（门牌号）
        注意：Placekey API只能聚合地址，不能提供unit number
        unit number只能从本地解析的公寓信息中提取
        
        Args:
            placekey_apartment_info: 本地公寓处理器分析的公寓信息
            existing_keywords: 原规则匹配的关键词
            
        Returns:
            提取的unit number字符串
        """
        unit_number = ''
        
        # 从本地公寓处理器的分析结果中提取unit number
        if placekey_apartment_info and self._safe_get(placekey_apartment_info, 'apartment_info'):
            apt_info = self._safe_get(placekey_apartment_info, 'apartment_info')
            if isinstance(apt_info, dict):
                # 提取房号信息
                number = self._safe_get(apt_info, 'number', '') if isinstance(apt_info, dict) else ''
                if number:
                    unit_number = str(number)
            elif isinstance(apt_info, str):
                # 如果是字符串，尝试解析
                import re
                # 匹配各种房号格式
                patterns = [
                    r'(?:APT|APARTMENT|UNIT|SUITE|STE)\s+([A-Z0-9]+)',
                    r'#\s*([A-Z0-9]+)',
                    r'([A-Z0-9]+)$'  # 末尾的房号
                ]
                for pattern in patterns:
                    match = re.search(pattern, apt_info.upper())
                    if match:
                        unit_number = match.group(1)
                        break
        
        # 如果还没有找到，尝试从关键词中提取
        if not unit_number and existing_keywords:
            import re
            # 从原规则匹配的关键词中提取房号
            patterns = [
                r'(?:apt|apartment|unit|suite|ste)\(([^)]+)\)',
                r'#\s*([A-Z0-9]+)',
                r'([A-Z0-9]+)'
            ]
            for pattern in patterns:
                match = re.search(pattern, existing_keywords, re.IGNORECASE)
                if match:
                    potential_code = match.group(1)
                    # 验证是否为有效的房号格式
                    if re.match(r'^[A-Z0-9]+$', potential_code.upper()):
                        unit_number = potential_code.upper()
                    break
        
        return unit_number
    
    def _generate_standardized_address(self, placekey_result: Optional[Dict], parsed_address: Dict) -> str:
        """
        生成标准化地址，用于统一公寓单元的基础地址
        
        Args:
            placekey_result: Placekey API返回的结果
            parsed_address: 解析后的地址信息
            
        Returns:
            标准化的基础地址（不包含单元号）
        """
        standardized_address = ''
        
        if placekey_result and isinstance(placekey_result, dict) and placekey_result.get('success'):
            # 优先使用Placekey API返回的matched_address
            matched_address = placekey_result.get('matched_address', {})
            if isinstance(matched_address, dict):
                # 从matched_address中提取基础地址信息
                street_address = matched_address.get('street_address', '')
                if street_address:
                    # 移除单元号信息，只保留基础地址
                    standardized_address = self._remove_unit_from_address(street_address)
            elif isinstance(matched_address, str) and matched_address:
                # 如果matched_address是字符串
                standardized_address = self._remove_unit_from_address(matched_address)
        
        # 如果Placekey没有返回有效地址，使用解析后的地址
        if not standardized_address and parsed_address:
            street_address = parsed_address.get('street_address', '')
            if street_address:
                standardized_address = self._remove_unit_from_address(street_address)
        
        return standardized_address
    
    def _remove_unit_from_address(self, address: str) -> str:
        """
        从地址中移除单元号信息，保留基础地址
        
        Args:
            address: 原始地址
            
        Returns:
            移除单元号后的基础地址
        """
        if not address:
            return ''
        
        import re
        
        # 定义各种单元号模式
        unit_patterns = [
            r'\s+(?:APT|APARTMENT|UNIT|SUITE|STE)\s+[A-Z0-9]+\s*$',  # 末尾的APT 123
            r'\s+#\s*[A-Z0-9]+\s*$',  # 末尾的#123
            r'\s+[A-Z0-9]+\s*$',  # 末尾的单独数字或字母
            r',\s*(?:APT|APARTMENT|UNIT|SUITE|STE)\s+[A-Z0-9]+',  # 逗号后的APT 123
            r',\s*#\s*[A-Z0-9]+',  # 逗号后的#123
        ]
        
        cleaned_address = address.strip()
        
        # 逐个应用模式移除单元号
        for pattern in unit_patterns:
            cleaned_address = re.sub(pattern, '', cleaned_address, flags=re.IGNORECASE)
        
        # 清理多余的空格和标点
        cleaned_address = re.sub(r'\s+', ' ', cleaned_address).strip()
        cleaned_address = cleaned_address.rstrip(',')
        
        return cleaned_address
    
    def _apply_maximization_principle(self, input_is_apt, input_confidence, input_keywords,
                                    rule_is_apt: bool, rule_confidence: int, rule_keywords: str) -> Tuple[bool, int, str]:
        """
        应用最大化原则，参考原有输入逻辑选择最佳结果
        
        Args:
            input_is_apt: 输入数据中的公寓判断结果
            input_confidence: 输入数据中的置信度
            input_keywords: 输入数据中的匹配关键词
            rule_is_apt: 规则引擎的公寓判断结果
            rule_confidence: 规则引擎的置信度
            rule_keywords: 规则引擎的匹配关键词
            
        Returns:
            最终选择的结果 (是否公寓, 置信度, 关键词)
        """
        try:
            # 处理输入数据的类型转换
            if input_is_apt is not None:
                if isinstance(input_is_apt, str):
                    input_is_apt = input_is_apt.lower() in ['true', '是', 'yes', '1']
                elif isinstance(input_is_apt, (int, float)):
                    input_is_apt = bool(input_is_apt)
            
            if input_confidence is not None:
                try:
                    input_confidence = int(float(input_confidence))
                except (ValueError, TypeError):
                    input_confidence = 0
            
            if input_keywords is None:
                input_keywords = ''
            
            # 最大化原则：宁可多输出也不要漏
            # 1. 如果任一方判断为公寓，则认为是公寓
            final_is_apt = False
            final_confidence = 0
            final_keywords = ''
            
            if input_is_apt or rule_is_apt:
                final_is_apt = True
                
                # 2. 选择更高的置信度
                if input_confidence and input_confidence > rule_confidence:
                    final_confidence = input_confidence
                    final_keywords = f"input({input_keywords})"
                    self.logger.info(f"采用输入数据结果: 置信度{input_confidence} > 规则{rule_confidence}")
                else:
                    final_confidence = rule_confidence
                    final_keywords = rule_keywords
                    if input_is_apt:
                        # 如果输入也认为是公寓，合并关键词
                        final_keywords = f"{rule_keywords}+input({input_keywords})"
                        self.logger.info(f"采用规则引擎结果，合并输入信息: {final_keywords}")
            else:
                # 3. 两者都不认为是公寓
                final_is_apt = False
                final_confidence = max(rule_confidence, input_confidence or 0)
                final_keywords = f"non_apt(rule:{rule_keywords},input:{input_keywords})"
            
            return final_is_apt, final_confidence, final_keywords
            
        except Exception as e:
            self.logger.error(f"_apply_maximization_principle异常: {str(e)}")
            # 返回安全的默认值
            return False, 0, f"error: {str(e)}"
     
    def _integrate_results(self, existing_is_apt: bool, existing_confidence: int, existing_keywords: str,
                          placekey_result: Optional[Dict], placekey_apartment_info: Optional[Dict]) -> Dict[str, Any]:
        """整合现有规则和Placekey结果"""
        self.logger.debug(f"_integrate_results开始: existing_is_apt={existing_is_apt}, existing_confidence={existing_confidence}, existing_keywords={existing_keywords}")
        # 严格的输入参数类型检查
        if not isinstance(existing_is_apt, bool):
            self.logger.error(f"existing_is_apt类型错误: {type(existing_is_apt)}")
            existing_is_apt = bool(existing_is_apt)
        
        if not isinstance(existing_confidence, (int, float)):
            self.logger.error(f"existing_confidence类型错误: {type(existing_confidence)}")
            existing_confidence = 0
        
        if not isinstance(existing_keywords, str):
            self.logger.error(f"existing_keywords类型错误: {type(existing_keywords)}")
            existing_keywords = str(existing_keywords) if existing_keywords else ""
        try:
            # 默认使用现有规则结果
            final_is_apartment = existing_is_apt
            final_confidence = existing_confidence
            final_keywords = existing_keywords
            status = "existing_only"
            conflict = False
            
            # 如果有Placekey结果，进行整合
            if placekey_apartment_info and self._safe_get(placekey_apartment_info, 'has_apartment') is not None:
                placekey_is_apt = self._safe_get(placekey_apartment_info, 'has_apartment', False)
                placekey_confidence = self._safe_get(placekey_apartment_info, 'confidence', 0)
                
                # 检查是否有冲突
                if existing_is_apt != placekey_is_apt:
                    conflict = True
                    self.stats['conflicts'] += 1
                    
                    # 冲突解决策略：选择置信度更高的结果
                    if placekey_confidence > existing_confidence:
                        final_is_apartment = placekey_is_apt
                        final_confidence = placekey_confidence
                        final_keywords = f"placekey_enhanced: {self._safe_get(placekey_apartment_info, 'apartment_type', '')}"
                        status = "placekey_override"
                    else:
                        status = "existing_override"
                else:
                    # 无冲突，使用更高的置信度
                    if placekey_confidence > existing_confidence:
                        final_confidence = placekey_confidence
                        final_keywords = f"{existing_keywords} + placekey_enhanced"
                        status = "both_agree_placekey_higher"
                    else:
                        status = "both_agree_existing_higher"
                
                self.stats['both_matches'] += 1
            else:
                # 只有现有规则有结果
                self.stats['existing_matches'] += 1
            
            # 严格的返回值类型检查
            result_dict = {
                'is_apartment': bool(final_is_apartment),
                'confidence': int(final_confidence) if isinstance(final_confidence, (int, float)) else 0,
                'keywords': str(final_keywords) if final_keywords else "",
                'status': str(status) if status else "unknown",
                'conflict': bool(conflict)
            }
            
            # 验证返回值是字典且包含所有必需键
            required_keys = ['is_apartment', 'confidence', 'keywords', 'status', 'conflict']
            for key in required_keys:
                if key not in result_dict:
                    self.logger.error(f"返回字典缺少键: {key}")
                    result_dict[key] = False if key in ['is_apartment', 'conflict'] else (0 if key == 'confidence' else "")
            
            self.logger.debug(f"_integrate_results正常返回: {result_dict}")
            return result_dict
            
        except Exception as e:
            self.logger.error(f"_integrate_results异常: {str(e)}")
            # 返回安全的默认值
            # 异常情况下的安全返回值
            safe_result = {
                'is_apartment': bool(existing_is_apt) if existing_is_apt is not None else False,
                'confidence': int(existing_confidence) if isinstance(existing_confidence, (int, float)) else 0,
                'keywords': str(existing_keywords) if existing_keywords else "",
                'status': 'error',
                'conflict': False
            }
            
            # 确保返回值是完整的字典
            self.logger.debug(f"_integrate_results异常返回: {safe_result}")
            return safe_result
    
    def _safe_get(self, data, key, default=''):
        """安全获取字典值，避免tuple错误"""
        if isinstance(data, dict):
            return data.get(key, default)
        return default
    
    def _safe_get_nested(self, data, keys, default=''):
        """安全获取嵌套字典值"""
        if not isinstance(data, dict):
            return default
        
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current if current is not None else default
    
    def _build_geocode_string(self, placekey_result):
        """安全构建geocode字符串"""
        if not isinstance(placekey_result, dict):
            return ''
        
        lat = self._safe_get(placekey_result, 'latitude', '')
        lng = self._safe_get(placekey_result, 'longitude', '')
        loc_type = self._safe_get(placekey_result, 'location_type', '')
        
        if lat:
            return f"lat:{lat},lng:{lng},type:{loc_type}"
        return ''
    
    def _update_stats(self, existing_is_apt: bool, placekey_apartment_info: Optional[Dict]):
        """更新统计信息"""
        if existing_is_apt:
            self.stats['existing_matches'] += 1
        
        if placekey_apartment_info and self._safe_get(placekey_apartment_info, 'has_apartment'):
            self.stats['placekey_matches'] += 1
    
    def _add_error_result(self, result: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """添加错误结果 - 确保包含所有必要的列"""
        result.update({
            # 原规则结果字段
            '是否公寓_原规则': False,
            '置信度_原规则': 0,
            '匹配关键词_原规则': '',
            
            # Placekey API返回的所有字段 - 完整字段集
            'placekey': '',
            'placekey_confidence': '',
            'placekey_matched_address': '',
            'placekey_success': False,
            'placekey_error': error_msg,
            'placekey_latitude': '',
            'placekey_longitude': '',
            'placekey_location_type': '',
            'placekey_address_components': '{}',
            
            # 单独提取重要的Placekey字段
            'address_placekey': '',
            'building_placekey': '',
            'geocode': '',
            'confidence': '',
            
            # 新增公寓分析字段
            '公寓类型_增强': 'NONE',
            '主地址_增强': '',
            '公寓信息_增强': '',
            
            # 地址标准化字段
            'standardized_address': '',
            
            # 直接的access code字段
            'access_code': '',
            
            # Placekey反向映射结果
            'reverse_mapping_success': False,
            'reverse_mapping_address': '',
            'reverse_mapping_coordinates': '',
            'reverse_mapping_latitude': '',
            'reverse_mapping_longitude': '',
            'reverse_mapping_error': '',
            
            # 整合后的最终结果
            '是否公寓_整合': False,
            '置信度_整合': 0,
            '匹配关键词_整合': '',
            '处理状态': 'error',
            '冲突标记': False,
            '错误信息': error_msg
        })
        return result
    
    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理整个DataFrame"""
        self.logger.info(f"开始处理 {len(df)} 条记录")
        
        # 重置统计
        self.stats = {key: 0 for key in self.stats.keys()}
        
        # 处理每一行
        processed_rows = []
        for index, row in df.iterrows():
            try:
                processed_row = self.process_single_address(row.to_dict())
                processed_rows.append(processed_row)
                
                if (index + 1) % 100 == 0:
                    self.logger.info(f"已处理 {index + 1} 条记录")
                    
            except Exception as e:
                self.logger.error(f"处理第 {index + 1} 行失败: {str(e)}")
                error_row = row.to_dict()
                error_row = self._add_error_result(error_row, f"行处理失败: {str(e)}")
                processed_rows.append(error_row)
        
        result_df = pd.DataFrame(processed_rows)
        
        # 打印统计信息
        self._print_stats()
        
        return result_df
    
    def _print_stats(self):
        """打印处理统计信息"""
        total = self.stats['total_processed']
        if total == 0:
            return
        
        self.logger.info("=== 处理统计 ===")
        self.logger.info(f"总记录数: {total}")
        self.logger.info(f"现有规则匹配: {self.stats['existing_matches']} ({self.stats['existing_matches']/total*100:.1f}%)")
        self.logger.info(f"Placekey匹配: {self.stats['placekey_matches']} ({self.stats['placekey_matches']/total*100:.1f}%)")
        self.logger.info(f"双重匹配: {self.stats['both_matches']} ({self.stats['both_matches']/total*100:.1f}%)")
        self.logger.info(f"结果冲突: {self.stats['conflicts']} ({self.stats['conflicts']/total*100:.1f}%)")
        self.logger.info(f"API错误: {self.stats['api_errors']} ({self.stats['api_errors']/total*100:.1f}%)")
        self.logger.info(f"反向映射成功: {self.stats['reverse_mapping_success']} ({self.stats['reverse_mapping_success']/total*100:.1f}%)")
        self.logger.info(f"反向映射错误: {self.stats['reverse_mapping_errors']} ({self.stats['reverse_mapping_errors']/total*100:.1f}%)")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return self.stats.copy()