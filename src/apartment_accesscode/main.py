#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行入口文件
提供用户友好的命令行界面
"""

import click
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any

from .config import config
from .placekey_client import PlacekeyClient, PlacekeyAPIError
from .address_processor import AddressProcessor
from .apartment_handler import ApartmentHandler
from .batch_processor import BatchProcessor

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """Placekey地址标准化工具
    
    基于Placekey API的地址标准化和公寓房号处理工具。
    """
    pass

@cli.command()
@click.option('--address', '-a', required=True, help='街道地址')
@click.option('--city', '-c', help='城市')
@click.option('--state', '-s', help='州/省份')
@click.option('--zip', '-z', help='邮编')
@click.option('--country', help='国家代码（默认US）', default='US')
@click.option('--latitude', type=float, help='纬度')
@click.option('--longitude', type=float, help='经度')
@click.option('--output', '-o', help='输出文件路径（JSON格式）')
@click.option('--verbose', '-v', is_flag=True, help='显示详细信息')
def single(address, city, state, zip, country, latitude, longitude, output, verbose):
    """处理单个地址"""
    try:
        # 验证配置
        validation = config.validate_config()
        if not validation['valid']:
            click.echo(f"配置错误: {', '.join(validation['issues'])}", err=True)
            sys.exit(1)
        
        # 构建地址数据
        address_data = {
            'street_address': address,
            'iso_country_code': country
        }
        
        if city:
            address_data['city'] = city
        if state:
            address_data['region'] = state
        if zip:
            address_data['postal_code'] = zip
        if latitude is not None and longitude is not None:
            address_data['latitude'] = latitude
            address_data['longitude'] = longitude
        
        # 初始化处理器
        processor = AddressProcessor()
        apartment_handler = ApartmentHandler()
        
        # 处理地址
        click.echo("正在处理地址...")
        result = processor.process_address(address_data)
        
        # 识别公寓信息
        apartment_info = apartment_handler.identify_apartment_type(address)
        
        # 合并结果
        final_result = {
            'input_address': address_data,
            'processing_result': result,
            'apartment_info': apartment_info,
            'timestamp': datetime.now().isoformat()
        }
        
        # 输出结果
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(final_result, f, indent=2, ensure_ascii=False)
            click.echo(f"结果已保存到: {output}")
        else:
            _display_single_result(final_result, verbose)
            
    except PlacekeyAPIError as e:
        click.echo(f"API错误: {str(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"处理失败: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--input', '-i', 'input_file', required=True, 
              help='输入CSV文件路径', type=click.Path(exists=True))
@click.option('--output', '-o', 'output_file', required=True, 
              help='输出CSV文件路径')
@click.option('--mapping', '-m', help='列名映射JSON文件路径', 
              type=click.Path(exists=True))
@click.option('--aggregate', is_flag=True, help='聚合公寓单元')
@click.option('--workers', '-w', default=5, help='并发工作线程数', type=int)
@click.option('--report', '-r', help='处理报告输出路径')
def batch(input_file, output_file, mapping, aggregate, workers, report):
    """批量处理CSV文件"""
    try:
        # 验证配置
        validation = config.validate_config()
        if not validation['valid']:
            click.echo(f"配置错误: {', '.join(validation['issues'])}", err=True)
            sys.exit(1)
        
        # 读取列名映射
        column_mapping = None
        if mapping:
            with open(mapping, 'r', encoding='utf-8') as f:
                mapping_data = json.load(f)
                # 提取mapping字段中的映射规则
                column_mapping = mapping_data.get('mapping', mapping_data)
        
        # 初始化批量处理器
        processor = BatchProcessor()
        
        # 处理文件
        click.echo(f"开始批量处理: {input_file}")
        click.echo(f"输出文件: {output_file}")
        click.echo(f"并发线程数: {workers}")
        click.echo(f"聚合公寓: {'是' if aggregate else '否'}")
        
        stats = processor.process_csv_file(
            input_file=input_file,
            output_file=output_file,
            column_mapping=column_mapping,
            aggregate_apartments=aggregate,
            max_workers=workers
        )
        
        # 显示统计信息
        _display_batch_stats(stats)
        
        # 保存处理报告
        if report:
            processor.save_processing_report(stats, report)
            click.echo(f"处理报告已保存到: {report}")
            
    except Exception as e:
        click.echo(f"批量处理失败: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--address', '-a', required=True, help='街道地址')
def apartment(address):
    """分析地址中的公寓信息"""
    try:
        apartment_handler = ApartmentHandler()
        
        # 识别公寓信息
        apartment_info = apartment_handler.identify_apartment_type(address)
        
        # 显示结果
        click.echo("\n=== 公寓信息分析 ===")
        click.echo(f"原始地址: {address}")
        click.echo(f"包含公寓信息: {'是' if apartment_info['has_apartment'] else '否'}")
        
        if apartment_info['has_apartment']:
            click.echo(f"公寓类型: {apartment_info['apartment_type']}")
            click.echo(f"主地址: {apartment_info['main_address']}")
            click.echo(f"置信度: {apartment_info['confidence']}%")
            
            apt_data = apartment_info['apartment_info']
            if apt_data:
                click.echo(f"单元类型: {apt_data['type']}")
                click.echo(f"单元号: {apt_data['number']}")
                click.echo(f"完整格式: {apt_data['full']}")
        
        # 显示地址变体
        variations = apartment_handler.extract_apartment_variations(address)
        if len(variations) > 1:
            click.echo("\n=== 地址变体 ===")
            for i, variation in enumerate(variations, 1):
                click.echo(f"{i}. {variation}")
        
        # 显示标准化格式
        click.echo("\n=== 标准化格式 ===")
        formats = ['standard', 'short', 'full']
        for fmt in formats:
            normalized = apartment_handler.normalize_apartment_format(address, fmt)
            click.echo(f"{fmt.capitalize()}: {normalized}")
            
    except Exception as e:
        click.echo(f"分析失败: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
def health():
    """检查API连接状态"""
    try:
        # 验证配置
        validation = config.validate_config()
        if not validation['valid']:
            click.echo(f"配置错误: {', '.join(validation['issues'])}", err=True)
            sys.exit(1)
        
        # 检查API连接
        client = PlacekeyClient()
        click.echo("正在检查API连接...")
        
        is_healthy = client.health_check()
        
        if is_healthy:
            click.echo("✅ API连接正常")
        else:
            click.echo("❌ API连接失败")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"健康检查失败: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
def config_info():
    """显示当前配置信息"""
    click.echo("=== 配置信息 ===")
    click.echo(f"API密钥: {'已设置' if config.PLACEKEY_API_KEY else '未设置'}")
    click.echo(f"API基础URL: {config.PLACEKEY_BASE_URL}")
    click.echo(f"批处理大小: {config.BATCH_SIZE}")
    click.echo(f"最大重试次数: {config.MAX_RETRIES}")
    click.echo(f"重试延迟: {config.RETRY_DELAY}秒")
    click.echo(f"日志级别: {config.LOG_LEVEL}")
    click.echo(f"日志文件: {config.LOG_FILE}")
    
    # 验证配置
    validation = config.validate_config()
    click.echo(f"\n配置状态: {'✅ 有效' if validation['valid'] else '❌ 无效'}")
    
    if not validation['valid']:
        click.echo("问题:")
        for issue in validation['issues']:
            click.echo(f"  - {issue}")

def _display_single_result(result: Dict[str, Any], verbose: bool = False):
    """显示单个地址处理结果"""
    click.echo("\n=== 处理结果 ===")
    
    # 显示输入地址
    input_addr = result['input_address']
    click.echo(f"输入地址: {input_addr.get('street_address', '')}")
    if input_addr.get('city'):
        click.echo(f"城市: {input_addr['city']}")
    if input_addr.get('region'):
        click.echo(f"州/省: {input_addr['region']}")
    if input_addr.get('postal_code'):
        click.echo(f"邮编: {input_addr['postal_code']}")
    
    # 显示Placekey结果
    placekey_result = result['processing_result'].get('placekey_result', {})
    if placekey_result.get('success'):
        click.echo(f"\n✅ Placekey: {placekey_result['placekey']}")
        click.echo(f"置信度: {placekey_result.get('confidence', 'unknown')}")
        
        matched_addr = placekey_result.get('matched_address', {})
        if matched_addr and verbose:
            click.echo("\n匹配的地址:")
            for key, value in matched_addr.items():
                click.echo(f"  {key}: {value}")
    else:
        click.echo(f"\n❌ 处理失败: {placekey_result.get('error', 'Unknown error')}")
    
    # 显示公寓信息
    apartment_info = result.get('apartment_info', {})
    if apartment_info.get('has_apartment'):
        click.echo(f"\n🏢 公寓信息:")
        click.echo(f"  类型: {apartment_info['apartment_type']}")
        click.echo(f"  主地址: {apartment_info['main_address']}")
        
        apt_data = apartment_info.get('apartment_info', {})
        if apt_data:
            click.echo(f"  单元: {apt_data['full']}")
    
    # 显示详细信息
    if verbose:
        validation = result['processing_result'].get('validation', {})
        click.echo(f"\n地址完整性: {validation.get('completeness_score', 0):.1f}%")
        
        missing_fields = validation.get('missing_fields', [])
        if missing_fields:
            click.echo(f"缺少字段: {', '.join(missing_fields)}")
        
        warnings = validation.get('warnings', [])
        if warnings:
            click.echo("警告:")
            for warning in warnings:
                click.echo(f"  - {warning}")

def _display_batch_stats(stats: Dict[str, Any]):
    """显示批量处理统计信息"""
    click.echo("\n=== 处理统计 ===")
    click.echo(f"总记录数: {stats['total_records']}")
    click.echo(f"成功处理: {stats['successful_records']}")
    click.echo(f"处理失败: {stats['failed_records']}")
    click.echo(f"成功率: {stats['success_rate']:.1f}%")
    click.echo(f"公寓地址: {stats['apartment_records']}")
    click.echo(f"非公寓地址: {stats['non_apartment_records']}")
    
    if stats.get('aggregated_buildings', 0) > 0:
        click.echo(f"聚合建筑物: {stats['aggregated_buildings']}")

def main():
    """主程序入口点"""
    cli()

if __name__ == '__main__':
    main()