#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
统一管理Placekey API项目的所有配置参数
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """项目配置类"""
    
    # API配置
    PLACEKEY_API_KEY = os.getenv('PLACEKEY_API_KEY', '')
    PLACEKEY_BASE_URL = os.getenv('PLACEKEY_BASE_URL', 'https://api.placekey.io/v1')
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/placekey.log')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 批处理配置
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '100'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY = float(os.getenv('RETRY_DELAY', '1.0'))
    
    # API请求配置
    REQUEST_TIMEOUT = 30
    REQUEST_HEADERS = {
        'Content-Type': 'application/json',
        'User-Agent': 'Placekey-Address-Processor/1.0'
    }
    
    # 地址字段映射
    ADDRESS_FIELDS = {
        'street_address': 'street_address',
        'city': 'city', 
        'region': 'region',
        'postal_code': 'postal_code',
        'iso_country_code': 'iso_country_code',
        'latitude': 'latitude',
        'longitude': 'longitude',
        'location_name': 'location_name'
    }
    
    # 公寓单元关键词
    APARTMENT_KEYWORDS = [
        'APT', 'APARTMENT',
        'UNIT', 'UN',
        'SUITE', 'STE', 'SU',
        'BUILDING', 'BLDG', 'BLD',
        'ROOM', 'RM',
        'FLOOR', 'FL', 'FLR',
        'LEVEL', 'LVL',
        'PENTHOUSE', 'PH'
    ]
    
    # 地址标准化规则
    ADDRESS_STANDARDIZATION = {
        'street_suffixes': {
            'ST': 'STREET',
            'AVE': 'AVENUE', 
            'BLVD': 'BOULEVARD',
            'RD': 'ROAD',
            'DR': 'DRIVE',
            'CT': 'COURT',
            'PL': 'PLACE',
            'LN': 'LANE',
            'WAY': 'WAY',
            'CIR': 'CIRCLE'
        },
        'directional': {
            'N': 'NORTH',
            'S': 'SOUTH', 
            'E': 'EAST',
            'W': 'WEST',
            'NE': 'NORTHEAST',
            'NW': 'NORTHWEST',
            'SE': 'SOUTHEAST',
            'SW': 'SOUTHWEST'
        }
    }
    
    @classmethod
    def validate_config(cls) -> Dict[str, Any]:
        """验证配置有效性"""
        issues = []
        
        if not cls.PLACEKEY_API_KEY:
            issues.append("PLACEKEY_API_KEY未设置")
            
        if cls.BATCH_SIZE <= 0:
            issues.append("BATCH_SIZE必须大于0")
            
        if cls.MAX_RETRIES < 0:
            issues.append("MAX_RETRIES不能小于0")
            
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    @classmethod
    def get_api_headers(cls) -> Dict[str, str]:
        """获取API请求头"""
        headers = cls.REQUEST_HEADERS.copy()
        if cls.PLACEKEY_API_KEY:
            headers['apikey'] = cls.PLACEKEY_API_KEY
        return headers

# 创建全局配置实例
config = Config()