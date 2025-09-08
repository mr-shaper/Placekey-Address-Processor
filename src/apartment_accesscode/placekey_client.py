#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Placekey API客户端
提供与Placekey API交互的核心功能
"""

import requests
import time
import logging
from typing import Dict, List, Optional, Union, Any
from .config import config

class PlacekeyAPIError(Exception):
    """Placekey API异常类"""
    pass

class PlacekeyClient:
    """Placekey API客户端类"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化Placekey客户端
        
        Args:
            api_key: Placekey API密钥，如果不提供则从配置中获取
        """
        self.api_key = api_key or config.PLACEKEY_API_KEY
        self.base_url = config.PLACEKEY_BASE_URL
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        
        if not self.api_key:
            raise PlacekeyAPIError("API密钥未设置，请在.env文件中配置PLACEKEY_API_KEY")
        
        # 设置请求头
        self.session.headers.update(config.get_api_headers())
    
    def _make_request(self, endpoint: str, data: Dict[str, Any], 
                     retries: int = None) -> Dict[str, Any]:
        """
        发送API请求
        
        Args:
            endpoint: API端点
            data: 请求数据
            retries: 重试次数
            
        Returns:
            API响应数据
        """
        if retries is None:
            retries = config.MAX_RETRIES
            
        url = f"{self.base_url}/{endpoint}"
        
        for attempt in range(retries + 1):
            try:
                response = self.session.post(
                    url, 
                    json=data, 
                    timeout=config.REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # 速率限制
                    if attempt < retries:
                        wait_time = config.RETRY_DELAY * (2 ** attempt)
                        self.logger.warning(f"API速率限制，等待{wait_time}秒后重试")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise PlacekeyAPIError("API速率限制，重试次数已用完")
                else:
                    error_msg = f"API请求失败: {response.status_code} - {response.text}"
                    raise PlacekeyAPIError(error_msg)
                    
            except requests.exceptions.RequestException as e:
                if attempt < retries:
                    wait_time = config.RETRY_DELAY * (2 ** attempt)
                    self.logger.warning(f"请求异常，等待{wait_time}秒后重试: {str(e)}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise PlacekeyAPIError(f"网络请求失败: {str(e)}")
        
        raise PlacekeyAPIError("请求失败，已达到最大重试次数")
    
    def get_placekey(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取单个地址的Placekey
        
        Args:
            address_data: 地址数据字典
            
        Returns:
            包含Placekey的响应数据
        """
        # 验证必要字段
        self._validate_address_data(address_data)
        
        # 构建请求数据
        request_data = {
            "query": self._format_address_query(address_data)
        }
        
        try:
            response = self._make_request("placekeys", request_data)
            return self._process_single_response(response, address_data)
        except Exception as e:
            self.logger.error(f"获取Placekey失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'input_address': address_data
            }
    
    def get_placekeys_batch(self, addresses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量获取Placekey
        
        Args:
            addresses: 地址数据列表
            
        Returns:
            Placekey结果列表
        """
        if not addresses:
            return []
        
        results = []
        batch_size = config.BATCH_SIZE
        
        # 分批处理
        for i in range(0, len(addresses), batch_size):
            batch = addresses[i:i + batch_size]
            batch_results = self._process_batch(batch)
            results.extend(batch_results)
            
            # 批次间延迟，避免API限制
            if i + batch_size < len(addresses):
                time.sleep(0.1)
        
        return results
    
    def _process_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理单个批次
        
        Args:
            batch: 批次地址数据
            
        Returns:
            批次处理结果
        """
        # 构建批量请求数据
        queries = []
        for i, address_data in enumerate(batch):
            try:
                self._validate_address_data(address_data)
                query = self._format_address_query(address_data)
                query['query_id'] = str(i)  # 添加查询ID用于匹配
                queries.append(query)
            except Exception as e:
                self.logger.warning(f"地址数据验证失败: {str(e)}")
                queries.append({
                    'query_id': str(i),
                    'error': str(e)
                })
        
        request_data = {"queries": queries}
        
        try:
            response = self._make_request("placekeys", request_data)
            return self._process_batch_response(response, batch)
        except Exception as e:
            self.logger.error(f"批量请求失败: {str(e)}")
            # 返回错误结果
            return [{
                'success': False,
                'error': str(e),
                'input_address': addr
            } for addr in batch]
    
    def _validate_address_data(self, address_data: Dict[str, Any]) -> None:
        """
        验证地址数据
        
        Args:
            address_data: 地址数据
            
        Raises:
            PlacekeyAPIError: 验证失败时抛出
        """
        if not isinstance(address_data, dict):
            raise PlacekeyAPIError("地址数据必须是字典格式")
        
        # 检查是否有坐标信息
        has_coordinates = ('latitude' in address_data and 
                          'longitude' in address_data and
                          address_data['latitude'] is not None and
                          address_data['longitude'] is not None)
        
        # 检查是否有地址信息
        has_address = any(field in address_data and address_data[field] 
                         for field in ['street_address', 'city', 'region', 'postal_code'])
        
        if not has_coordinates and not has_address:
            raise PlacekeyAPIError("必须提供坐标信息或地址信息")
    
    def _format_address_query(self, address_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化地址查询数据
        
        Args:
            address_data: 原始地址数据
            
        Returns:
            格式化后的查询数据
        """
        query = {}
        
        # 映射标准字段
        for field, api_field in config.ADDRESS_FIELDS.items():
            if field in address_data and address_data[field] is not None:
                value = str(address_data[field]).strip()
                if value:
                    query[api_field] = value
        
        return query
    
    def _process_single_response(self, response: Dict[str, Any], 
                               input_address: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理单个地址响应
        
        Args:
            response: API响应
            input_address: 输入地址
            
        Returns:
            处理后的结果
        """
        if 'placekey' in response:
            return {
                'success': True,
                'placekey': response['placekey'],
                'input_address': input_address,
                'matched_address': response.get('matched_address', {}),
                'confidence': response.get('confidence', 'unknown')
            }
        else:
            return {
                'success': False,
                'error': 'No placekey returned',
                'input_address': input_address,
                'response': response
            }
    
    def _process_batch_response(self, response: Dict[str, Any], 
                              input_batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理批量响应
        
        Args:
            response: API批量响应
            input_batch: 输入批次数据
            
        Returns:
            处理后的结果列表
        """
        results = []
        
        if 'results' in response:
            for result in response['results']:
                query_id = int(result.get('query_id', 0))
                input_address = input_batch[query_id] if query_id < len(input_batch) else {}
                
                if 'placekey' in result:
                    results.append({
                        'success': True,
                        'placekey': result['placekey'],
                        'input_address': input_address,
                        'matched_address': result.get('matched_address', {}),
                        'confidence': result.get('confidence', 'unknown')
                    })
                else:
                    results.append({
                        'success': False,
                        'error': result.get('error', 'No placekey returned'),
                        'input_address': input_address
                    })
        else:
            # 如果没有results字段，为每个输入返回错误
            for input_address in input_batch:
                results.append({
                    'success': False,
                    'error': 'Invalid batch response format',
                    'input_address': input_address
                })
        
        return results
    
    def health_check(self) -> bool:
        """
        检查API连接状态
        
        Returns:
            连接是否正常
        """
        try:
            # 使用一个简单的地址进行测试
            test_address = {
                'street_address': '1 Hacker Way',
                'city': 'Menlo Park',
                'region': 'CA',
                'postal_code': '94025',
                'iso_country_code': 'US'
            }
            
            result = self.get_placekey(test_address)
            return result.get('success', False)
        except Exception as e:
            self.logger.error(f"健康检查失败: {str(e)}")
            return False