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
                       standardize: bool = True, 
                       use_precision_optimization: bool = True) -> Dict[str, Any]:
        """
        处理单个地址
        
        Args:
            address_data: 原始地址数据
            standardize: 是否进行标准化处理
            use_precision_optimization: 是否使用精度优化
            
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
            
            # 4. 获取Placekey（使用精度优化或标准方法）
            if use_precision_optimization:
                placekey_result = self.get_optimized_placekey(address_data)
            else:
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
    
    def get_optimized_placekey(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取优化的Placekey结果
        使用多种策略来提高地址精度
        
        Args:
            address_data: 地址数据
            
        Returns:
            优化后的Placekey结果
        """
        strategies = []
        
        # 策略1: 原始地址
        strategies.append({
            'name': '原始地址',
            'data': address_data,
            'priority': 1
        })
        
        # 策略2: 移除公寓号（如果存在）
        if 'street_address' in address_data:
            main_addr, apt_unit = self.extract_apartment_info(address_data['street_address'])
            if apt_unit:  # 如果有公寓号
                no_apt_data = address_data.copy()
                no_apt_data['street_address'] = main_addr.strip()
                strategies.append({
                    'name': '移除公寓号',
                    'data': no_apt_data,
                    'priority': 2
                })
        
        # 策略3: 标准化地址
        cleaned = self.clean_address_data(address_data)
        standardized = self.standardize_address(cleaned)
        strategies.append({
            'name': '标准化地址',
            'data': standardized,
            'priority': 3
        })
        
        # 执行所有策略并评估结果
        results = []
        for strategy in strategies:
            try:
                result = self.client.get_placekey(strategy['data'])
                if result.get('success'):
                    # 计算精度评分
                    precision_score = self._calculate_precision_score(result)
                    result['strategy_name'] = strategy['name']
                    result['strategy_priority'] = strategy['priority']
                    result['precision_score'] = precision_score
                    result['test_address'] = strategy['data']
                    results.append(result)
            except Exception as e:
                self.logger.warning(f"策略 '{strategy['name']}' 失败: {str(e)}")
        
        if not results:
            return {
                'success': False,
                'error': '所有策略都失败了',
                'strategies_tested': len(strategies)
            }
        
        # 选择最佳结果
        best_result = self._select_best_placekey_result(results)
        
        # 添加精度分析信息
        best_result['precision_analysis'] = {
            'strategies_tested': len(strategies),
            'successful_strategies': len(results),
            'all_results': results,
            'precision_notes': self._generate_precision_notes(results)
        }
        
        return best_result
    
    def _calculate_precision_score(self, result: Dict[str, Any]) -> float:
        """
        计算Placekey结果的精度评分
        
        Args:
            result: Placekey API结果
            
        Returns:
            精度评分 (0-100)
        """
        if not result.get('success'):
            return 0.0
        
        score = 50.0  # 基础分
        
        # 根据位置类型调整分数
        location_type = result.get('location_type', '').upper()
        if location_type == 'ROOFTOP':
            score += 40  # 最高精度 - 精确到建筑物屋顶
        elif location_type == 'RANGE_INTERPOLATED':
            score += 20  # 中等精度 - 基于地址范围插值
        elif location_type == 'GEOMETRIC_CENTER':
            score += 10  # 较低精度 - 几何中心
        elif location_type == 'APPROXIMATE':
            score += 5   # 最低精度 - 近似位置
        
        # 根据置信度调整分数
        confidence = result.get('confidence', '').lower()
        if confidence == 'high':
            score += 10
        elif confidence == 'medium':
            score += 5
        
        # 如果有坐标信息，加分
        if result.get('latitude') and result.get('longitude'):
            score += 5
        
        # 如果有building_placekey，说明精度更高
        if result.get('matched_address', {}).get('building_placekey'):
            score += 5
        
        return min(score, 100.0)
    
    def _select_best_placekey_result(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        从多个Placekey结果中选择最佳的
        
        Args:
            results: Placekey结果列表
            
        Returns:
            最佳结果
        """
        if not results:
            return {'success': False, 'error': 'No valid results'}
        
        # 按精度评分排序，评分相同时按策略优先级排序
        results.sort(key=lambda x: (x.get('precision_score', 0), -x.get('strategy_priority', 999)), reverse=True)
        
        return results[0]
    
    def _generate_precision_notes(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        生成精度说明
        
        Args:
            results: 所有结果
            
        Returns:
            精度说明列表
        """
        notes = []
        
        if not results:
            return ['无法获取任何Placekey结果']
        
        # 分析位置类型
        location_types = [r.get('location_type', 'unknown') for r in results]
        unique_types = set(location_types)
        
        if 'ROOFTOP' in unique_types:
            notes.append('获得了屋顶级别的高精度定位')
        elif all(lt == 'RANGE_INTERPOLATED' for lt in location_types):
            notes.append('所有结果都是基于地址范围插值，说明该地址在数据库中没有精确的GPS记录')
            notes.append('这可能导致门牌号与实际位置存在偏差（如2270变成2260）')
        
        # 分析Placekey一致性
        unique_placekeys = set(r.get('placekey', '') for r in results)
        if len(unique_placekeys) > 1:
            notes.append(f'不同地址格式产生了{len(unique_placekeys)}个不同的Placekey')
            notes.append('已选择精度评分最高的结果')
        else:
            notes.append('所有地址格式产生相同的Placekey，结果一致性良好')
        
        # 精度评分说明
        best_score = max(r.get('precision_score', 0) for r in results)
        if best_score >= 90:
            notes.append(f'精度评分{best_score:.1f}/100，定位精度很高')
        elif best_score >= 70:
            notes.append(f'精度评分{best_score:.1f}/100，定位精度良好')
        elif best_score >= 50:
            notes.append(f'精度评分{best_score:.1f}/100，定位精度一般，建议谨慎使用')
        else:
            notes.append(f'精度评分{best_score:.1f}/100，定位精度较低')
        
        return notes
    
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