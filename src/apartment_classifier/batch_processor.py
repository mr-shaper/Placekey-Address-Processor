#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量地址处理模块
支持CSV文件的批量处理和结果导出
"""

import pandas as pd
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

from . import config as config_module
from .placekey_client import PlacekeyClient
from .address_processor import AddressProcessor
from .apartment_handler import ApartmentHandler

class BatchProcessor:
    """批量地址处理器类"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化批量处理器
        
        Args:
            api_key: Placekey API密钥
        """
        self.client = PlacekeyClient(api_key)
        self.address_processor = AddressProcessor(self.client)
        self.apartment_handler = ApartmentHandler()
        self.logger = logging.getLogger(__name__)
        
        # 设置日志
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志配置"""
        # 创建logs目录
        log_dir = os.path.dirname(config_module.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 配置日志格式
        logging.basicConfig(
            level=getattr(logging, config_module.LOG_LEVEL),
            format=config_module.LOG_FORMAT,
            handlers=[
                logging.FileHandler(config_module.LOG_FILE, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def process_csv_file(self, input_file: str, output_file: str, 
                        column_mapping: Optional[Dict[str, str]] = None,
                        aggregate_apartments: bool = False,
                        max_workers: int = 5) -> Dict[str, Any]:
        """
        处理CSV文件
        
        Args:
            input_file: 输入CSV文件路径
            output_file: 输出CSV文件路径
            column_mapping: 列名映射字典
            aggregate_apartments: 是否聚合公寓单元
            max_workers: 最大并发工作线程数
            
        Returns:
            处理结果统计
        """
        try:
            # 读取CSV文件
            self.logger.info(f"开始读取文件: {input_file}")
            df = pd.read_csv(input_file, encoding='utf-8')
            
            if df.empty:
                raise ValueError("输入文件为空")
            
            self.logger.info(f"成功读取 {len(df)} 条记录")
            
            # 应用列名映射
            if column_mapping:
                df = df.rename(columns=column_mapping)
            
            # 验证必要列
            required_columns = self._get_required_columns(df.columns.tolist())
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.logger.warning(f"缺少推荐列: {missing_columns}")
            
            # 转换为地址记录列表
            address_records = self._dataframe_to_address_records(df)
            
            # 处理地址记录
            if max_workers > 1:
                results = self._process_addresses_parallel(address_records, max_workers)
            else:
                results = self._process_addresses_sequential(address_records)
            
            # 处理公寓聚合
            if aggregate_apartments:
                results = self._aggregate_apartment_results(results)
            
            # 保存结果
            self._save_results_to_csv(results, output_file)
            
            # 生成统计报告
            stats = self._generate_processing_stats(results)
            
            self.logger.info(f"批量处理完成，结果已保存到: {output_file}")
            return stats
            
        except Exception as e:
            self.logger.error(f"批量处理失败: {str(e)}")
            raise
    
    def _get_required_columns(self, available_columns: List[str]) -> List[str]:
        """获取推荐的必要列"""
        # 标准地址字段
        standard_fields = ['street_address', 'city', 'region', 'postal_code', 'iso_country_code']
        
        # 检查可用列中的地址相关字段
        address_related = []
        for col in available_columns:
            col_lower = col.lower()
            if any(field in col_lower for field in ['address', 'street', 'city', 'state', 'zip', 'postal']):
                address_related.append(col)
        
        return standard_fields if not address_related else address_related
    
    def _dataframe_to_address_records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """将DataFrame转换为地址记录列表"""
        records = []
        
        for index, row in df.iterrows():
            # 构建地址记录
            address_record = {
                'row_index': index,
                'original_data': row.to_dict()
            }
            
            # 提取地址字段
            address_data = {}
            for field in config_module.ADDRESS_FIELDS.keys():
                if field in row and pd.notna(row[field]):
                    address_data[field] = str(row[field]).strip()
            
            # 尝试从其他列名推断地址字段
            if not address_data.get('street_address'):
                for col in row.index:
                    col_lower = col.lower()
                    if 'address' in col_lower or 'street' in col_lower:
                        if pd.notna(row[col]):
                            address_data['street_address'] = str(row[col]).strip()
                            break
            
            if not address_data.get('city'):
                for col in row.index:
                    if 'city' in col.lower() and pd.notna(row[col]):
                        address_data['city'] = str(row[col]).strip()
                        break
            
            if not address_data.get('region'):
                for col in row.index:
                    col_lower = col.lower()
                    if 'state' in col_lower or 'region' in col_lower:
                        if pd.notna(row[col]):
                            address_data['region'] = str(row[col]).strip()
                            break
            
            if not address_data.get('postal_code'):
                for col in row.index:
                    col_lower = col.lower()
                    if 'zip' in col_lower or 'postal' in col_lower:
                        if pd.notna(row[col]):
                            address_data['postal_code'] = str(row[col]).strip()
                            break
            
            address_record['address_data'] = address_data
            records.append(address_record)
        
        return records
    
    def _process_addresses_sequential(self, address_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """顺序处理地址记录"""
        results = []
        
        with tqdm(total=len(address_records), desc="处理地址") as pbar:
            for record in address_records:
                try:
                    result = self._process_single_address_record(record)
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"处理记录 {record['row_index']} 失败: {str(e)}")
                    results.append({
                        'row_index': record['row_index'],
                        'success': False,
                        'error': str(e),
                        'original_data': record['original_data']
                    })
                
                pbar.update(1)
        
        return results
    
    def _process_addresses_parallel(self, address_records: List[Dict[str, Any]], 
                                  max_workers: int) -> List[Dict[str, Any]]:
        """并行处理地址记录"""
        results = [None] * len(address_records)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            future_to_index = {
                executor.submit(self._process_single_address_record, record): i 
                for i, record in enumerate(address_records)
            }
            
            # 处理完成的任务
            with tqdm(total=len(address_records), desc="处理地址") as pbar:
                for future in as_completed(future_to_index):
                    index = future_to_index[future]
                    try:
                        result = future.result()
                        results[index] = result
                    except Exception as e:
                        self.logger.error(f"处理记录 {index} 失败: {str(e)}")
                        results[index] = {
                            'row_index': index,
                            'success': False,
                            'error': str(e),
                            'original_data': address_records[index]['original_data']
                        }
                    
                    pbar.update(1)
        
        return results
    
    def _process_single_address_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个地址记录"""
        address_data = record['address_data']
        
        # 1. 识别公寓信息
        apartment_info = None
        if 'street_address' in address_data:
            apartment_info = self.apartment_handler.identify_apartment_type(
                address_data['street_address']
            )
        
        # 2. 处理地址
        processing_result = self.address_processor.process_address(address_data)
        
        # 3. 合并结果
        result = {
            'row_index': record['row_index'],
            'success': processing_result.get('placekey_result', {}).get('success', False),
            'original_data': record['original_data'],
            'address_processing': processing_result,
            'apartment_info': apartment_info,
            'timestamp': datetime.now().isoformat()
        }
        
        # 4. 提取关键信息到顶层
        placekey_result = processing_result.get('placekey_result', {})
        if placekey_result.get('success'):
            result['placekey'] = placekey_result.get('placekey')
            result['matched_address'] = placekey_result.get('matched_address', {})
            result['confidence'] = placekey_result.get('confidence')
        else:
            result['error'] = placekey_result.get('error', 'Unknown error')
        
        return result
    
    def _aggregate_apartment_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """聚合公寓结果"""
        # 按建筑物分组
        building_groups = {}
        non_apartment_results = []
        
        for result in results:
            apartment_info = result.get('apartment_info')
            
            if apartment_info and apartment_info.get('has_apartment'):
                main_address = apartment_info.get('main_address', '')
                if main_address:
                    if main_address not in building_groups:
                        building_groups[main_address] = []
                    building_groups[main_address].append(result)
                else:
                    non_apartment_results.append(result)
            else:
                non_apartment_results.append(result)
        
        # 处理聚合
        aggregated_results = []
        
        for main_address, group in building_groups.items():
            if len(group) > 1:
                # 创建聚合记录
                building_summary = self.apartment_handler.create_building_summary([
                    {'main_address': main_address, 'apartment_info': r.get('apartment_info', {})}
                    for r in group
                ])
                
                # 为建筑物主地址获取Placekey
                try:
                    main_address_data = {'street_address': main_address}
                    building_placekey = self.client.get_placekey(main_address_data)
                    
                    aggregated_result = {
                        'aggregated': True,
                        'building_address': main_address,
                        'building_placekey': building_placekey.get('placekey') if building_placekey.get('success') else None,
                        'total_units': len(group),
                        'individual_results': group,
                        'building_summary': building_summary,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    aggregated_results.append(aggregated_result)
                    
                except Exception as e:
                    self.logger.warning(f"获取建筑物Placekey失败: {str(e)}")
                    # 如果聚合失败，保留原始结果
                    aggregated_results.extend(group)
            else:
                # 单个公寓，不需要聚合
                aggregated_results.extend(group)
        
        # 添加非公寓结果
        aggregated_results.extend(non_apartment_results)
        
        return aggregated_results
    
    def _save_results_to_csv(self, results: List[Dict[str, Any]], output_file: str):
        """保存结果到CSV文件"""
        # 准备输出数据
        output_data = []
        
        for result in results:
            if result.get('aggregated'):
                # 聚合结果
                row = {
                    'type': 'building_aggregate',
                    'building_address': result.get('building_address'),
                    'building_placekey': result.get('building_placekey'),
                    'total_units': result.get('total_units'),
                    'processing_timestamp': result.get('timestamp')
                }
                output_data.append(row)
                
                # 添加各个单元的详细信息
                for unit_result in result.get('individual_results', []):
                    unit_row = self._result_to_output_row(unit_result)
                    unit_row['parent_building'] = result.get('building_address')
                    unit_row['parent_building_placekey'] = result.get('building_placekey')
                    output_data.append(unit_row)
            else:
                # 普通结果
                output_data.append(self._result_to_output_row(result))
        
        # 转换为DataFrame并保存
        output_df = pd.DataFrame(output_data)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_df.to_csv(output_file, index=False, encoding='utf-8')
        self.logger.info(f"结果已保存到: {output_file}")
    
    def _result_to_output_row(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """将处理结果转换为输出行"""
        row = {
            'row_index': result.get('row_index'),
            'success': result.get('success'),
            'placekey': result.get('placekey'),
            'confidence': result.get('confidence'),
            'error': result.get('error'),
            'processing_timestamp': result.get('timestamp')
        }
        
        # 添加原始数据
        original_data = result.get('original_data', {})
        for key, value in original_data.items():
            row[f'original_{key}'] = value
        
        # 添加处理后的地址信息
        address_processing = result.get('address_processing', {})
        standardized_address = address_processing.get('standardized_address', {})
        for key, value in standardized_address.items():
            row[f'standardized_{key}'] = value
        
        # 添加匹配的地址信息
        matched_address = result.get('matched_address', {})
        for key, value in matched_address.items():
            row[f'matched_{key}'] = value
        
        # 添加公寓信息
        apartment_info = result.get('apartment_info', {})
        if apartment_info and apartment_info.get('has_apartment'):
            row['has_apartment'] = True
            row['apartment_type'] = apartment_info.get('apartment_type')
            row['main_address'] = apartment_info.get('main_address')
            
            apt_data = apartment_info.get('apartment_info', {})
            if apt_data:
                row['apartment_unit_type'] = apt_data.get('type')
                row['apartment_unit_number'] = apt_data.get('number')
                row['apartment_full'] = apt_data.get('full')
                # 添加unit_number字段，使用apartment_unit_number作为unit_number
                row['unit_number'] = apt_data.get('number', '')
        else:
            row['has_apartment'] = False
            row['unit_number'] = ''
        
        return row
    
    def _generate_processing_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成处理统计信息"""
        total_records = len(results)
        successful_records = sum(1 for r in results if r.get('success'))
        failed_records = total_records - successful_records
        
        apartment_records = sum(1 for r in results 
                              if r.get('apartment_info', {}).get('has_apartment'))
        
        aggregated_buildings = sum(1 for r in results if r.get('aggregated'))
        
        stats = {
            'total_records': total_records,
            'successful_records': successful_records,
            'failed_records': failed_records,
            'success_rate': (successful_records / total_records * 100) if total_records > 0 else 0,
            'apartment_records': apartment_records,
            'non_apartment_records': total_records - apartment_records,
            'aggregated_buildings': aggregated_buildings,
            'processing_timestamp': datetime.now().isoformat()
        }
        
        return stats
    
    def save_processing_report(self, stats: Dict[str, Any], report_file: str):
        """保存处理报告"""
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"处理报告已保存到: {report_file}")
        except Exception as e:
            self.logger.error(f"保存处理报告失败: {str(e)}")