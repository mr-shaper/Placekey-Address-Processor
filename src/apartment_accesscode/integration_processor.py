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

from .config import config
from .placekey_client import PlacekeyClient, PlacekeyAPIError
from .address_processor import AddressProcessor
from .apartment_handler import ApartmentHandler

class ExistingApartmentClassifier:
    """现有公寓识别规则实现"""
    
    def __init__(self):
        """初始化分类器"""
        self.logger = logging.getLogger(__name__)
        self._compile_patterns()
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        # 高置信度关键词 (95%)
        self.high_confidence_keywords = [
            'apartment', 'apt', 'unit', 'suite', 'ste',
            'penthouse', 'ph', 'studio', 'loft', 'basement', 'bsmt',
            'floor', 'fl', 'level', 'lvl'
        ]
        
        # 中等置信度关键词 (80%)
        self.medium_confidence_keywords = [
            'building', 'bldg', 'room', 'rm',
            'department', 'dept', 'office', 'ofc',
            'condo', 'condominium'
        ]
        
        # 低置信度关键词 (60%)
        self.low_confidence_keywords = [
            'trailer', 'trlr', 'lobby', 'lbby',
            'north', 'south', 'east', 'west',
            'upper', 'lower', 'side', 'left', 'right', 'front', 'rear',
            'pier', 'slip', 'space', 'key', 'lot'
        ]
        
        # 需要验证关键词 (40%)
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
            'hill', 'heights', 'hts', 'valley', 'view', 'lake', 'river'
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
        """检查上下文排除规则"""
        # 检查关键词前后3个词内是否有街道类型
        words = address.lower().split()
        
        try:
            # 找到关键词在单词列表中的位置
            keyword_indices = []
            for i, word in enumerate(words):
                if keyword.lower() in word.lower():
                    keyword_indices.append(i)
            
            for idx in keyword_indices:
                # 检查前后3个词
                start = max(0, idx - 3)
                end = min(len(words), idx + 4)
                
                context_words = words[start:end]
                context_text = ' '.join(context_words)
                
                if self.street_pattern.search(context_text):
                    return True  # 需要排除
            
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
        
        # 检查高置信度关键词 (95%)
        for keyword in self.high_confidence_keywords:
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            match = pattern.search(street_address)
            if match:
                max_confidence = max(max_confidence, 95)
                matched_keywords.append(f"{keyword}({match.group()})")
        
        # 检查中等置信度关键词 (80%)
        for keyword in self.medium_confidence_keywords:
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            match = pattern.search(street_address)
            if match:
                max_confidence = max(max_confidence, 80)
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
        
        # 检查低置信度关键词 (60%) - 需要上下文验证
        for keyword in self.low_confidence_keywords:
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            match = pattern.search(street_address)
            if match:
                # 检查上下文排除
                if not self.check_context_exclusion(street_address, keyword, match.start()):
                    max_confidence = max(max_confidence, 60)
                    matched_keywords.append(f"{keyword}({match.group()})")
        
        # 检查需要验证关键词 (40%)
        for keyword in self.verification_keywords:
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            match = pattern.search(street_address)
            if match:
                max_confidence = max(max_confidence, 40)
                matched_keywords.append(f"{keyword}({match.group()})")
        
        # 判断结果
        is_apartment = max_confidence >= 50
        matched_keywords_str = ", ".join(matched_keywords) if matched_keywords else ""
        
        return is_apartment, max_confidence, matched_keywords_str

class IntegrationProcessor:
    """整合处理器 - 结合现有规则与Placekey API"""
    
    def __init__(self):
        """初始化处理器"""
        self.logger = logging.getLogger(__name__)
        
        # 初始化各个组件
        self.existing_classifier = ExistingApartmentClassifier()
        self.placekey_processor = AddressProcessor()
        self.apartment_handler = ApartmentHandler()
        
        # 统计信息
        self.stats = {
            'total_processed': 0,
            'existing_matches': 0,
            'placekey_matches': 0,
            'both_matches': 0,
            'conflicts': 0,
            'api_errors': 0
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
            # 解析地址格式
            full_address = address_data.get('地址', '')
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
            existing_is_apt, existing_confidence, existing_keywords = \
                self._apply_maximization_principle(
                    input_is_apt, input_confidence, input_keywords,
                    rule_is_apt, rule_confidence, rule_keywords
                )
            
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
                    placekey_result = self.placekey_processor.process_address(placekey_data)
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
            integrated_result = self._integrate_results(
                existing_is_apt, existing_confidence, existing_keywords,
                placekey_result, placekey_apartment_info
            )
            
            # 4. 更新统计
            self._update_stats(existing_is_apt, placekey_apartment_info)
            
            # 5. 提取access code信息
            access_code = self._extract_access_code(placekey_apartment_info, existing_keywords)
            
            # 6. 添加增强信息到结果
            result.update({
                # 保留原有字段
                '是否公寓_原规则': existing_is_apt,
                '置信度_原规则': existing_confidence,
                '匹配关键词_原规则': existing_keywords,
                
                # 新增Placekey增强字段
                'placekey': placekey_result.get('placekey_result', {}).get('placekey', '') if placekey_result else '',
                'placekey_confidence': placekey_result.get('placekey_result', {}).get('confidence', '') if placekey_result else '',
                'placekey_success': placekey_result.get('placekey_result', {}).get('success', False) if placekey_result else False,
                
                # 新增公寓分析字段
                '公寓类型_增强': placekey_apartment_info.get('apartment_type', 'NONE') if placekey_apartment_info else 'NONE',
                '主地址_增强': placekey_apartment_info.get('main_address', '') if placekey_apartment_info else '',
                '公寓信息_增强': str(placekey_apartment_info.get('apartment_info', {})) if placekey_apartment_info else '',
                
                # 直接的access code字段
                'access_code': access_code,
                
                # 整合后的最终结果
                '是否公寓_整合': integrated_result['is_apartment'],
                '置信度_整合': integrated_result['confidence'],
                '匹配关键词_整合': integrated_result['keywords'],
                '处理状态': integrated_result['status'],
                '冲突标记': integrated_result['conflict']
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"处理地址失败: {str(e)}")
            return self._add_error_result(result, f"处理失败: {str(e)}")
    
    def _extract_access_code(self, placekey_apartment_info: Optional[Dict], existing_keywords: str) -> str:
        """
        提取access code信息
        
        Args:
            placekey_apartment_info: Placekey增强的公寓信息
            existing_keywords: 原规则匹配的关键词
            
        Returns:
            提取的access code字符串
        """
        access_code = ''
        
        # 优先从Placekey增强信息中提取
        if placekey_apartment_info and placekey_apartment_info.get('apartment_info'):
            apt_info = placekey_apartment_info['apartment_info']
            if isinstance(apt_info, dict):
                # 提取房号信息
                number = apt_info.get('number', '')
                if number:
                    access_code = str(number)
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
                        access_code = match.group(1)
                        break
        
        # 如果Placekey没有提取到，从原规则关键词中提取
        if not access_code and existing_keywords:
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
                        access_code = potential_code.upper()
                        break
        
        return access_code
    
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
     
    def _integrate_results(self, existing_is_apt: bool, existing_confidence: int, existing_keywords: str,
                          placekey_result: Optional[Dict], placekey_apartment_info: Optional[Dict]) -> Dict[str, Any]:
        """整合现有规则和Placekey结果"""
        # 默认使用现有规则结果
        final_is_apartment = existing_is_apt
        final_confidence = existing_confidence
        final_keywords = existing_keywords
        status = "existing_only"
        conflict = False
        
        # 如果有Placekey结果，进行整合
        if placekey_apartment_info and placekey_apartment_info.get('has_apartment') is not None:
            placekey_is_apt = placekey_apartment_info.get('has_apartment', False)
            placekey_confidence = placekey_apartment_info.get('confidence', 0)
            
            # 检查是否有冲突
            if existing_is_apt != placekey_is_apt:
                conflict = True
                self.stats['conflicts'] += 1
                
                # 冲突解决策略：选择置信度更高的结果
                if placekey_confidence > existing_confidence:
                    final_is_apartment = placekey_is_apt
                    final_confidence = placekey_confidence
                    final_keywords = f"placekey_enhanced: {placekey_apartment_info.get('apartment_type', '')}"
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
        
        return {
            'is_apartment': final_is_apartment,
            'confidence': final_confidence,
            'keywords': final_keywords,
            'status': status,
            'conflict': conflict
        }
    
    def _update_stats(self, existing_is_apt: bool, placekey_apartment_info: Optional[Dict]):
        """更新统计信息"""
        if existing_is_apt:
            self.stats['existing_matches'] += 1
        
        if placekey_apartment_info and placekey_apartment_info.get('has_apartment'):
            self.stats['placekey_matches'] += 1
    
    def _add_error_result(self, result: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """添加错误结果"""
        result.update({
            '处理状态': 'error',
            '错误信息': error_msg,
            '是否公寓_整合': False,
            '置信度_整合': 0,
            '匹配关键词_整合': '',
            '冲突标记': False
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
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return self.stats.copy()