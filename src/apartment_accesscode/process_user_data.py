#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户数据处理工具
专门处理用户现有的CSV数据格式，整合现有公寓识别规则与Placekey API
"""

import click
import pandas as pd
import os
import sys
from datetime import datetime
import json
from typing import Dict, Any

from .integration_processor import IntegrationProcessor
from . import config as config_module_file

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """用户数据处理工具
    
    整合现有公寓识别规则与Placekey API，处理用户现有数据格式。
    """
    pass

@cli.command()
@click.option('--input', '-i', 'input_file', required=True, 
              help='输入CSV文件路径', type=click.Path(exists=True))
@click.option('--output', '-o', 'output_file', required=True, 
              help='输出CSV文件路径')
@click.option('--sample', '-s', type=int, help='处理样本数量（用于测试）')
@click.option('--report', '-r', help='处理报告输出路径')
@click.option('--verbose', '-v', is_flag=True, help='显示详细信息')
def process(input_file, output_file, sample, report, verbose):
    """处理用户CSV数据文件"""
    try:
        # 验证配置
        validation = config_module_file.validate_config()
        if not validation['valid']:
            click.echo(f"配置警告: {', '.join(validation['issues'])}", err=True)
            click.echo("部分功能可能受限，但现有规则仍可正常工作")
        
        # 读取CSV文件
        click.echo(f"正在读取文件: {input_file}")
        try:
            df = pd.read_csv(input_file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(input_file, encoding='gbk')
                click.echo("使用GBK编码读取文件")
            except UnicodeDecodeError:
                df = pd.read_csv(input_file, encoding='gb2312')
                click.echo("使用GB2312编码读取文件")
        
        click.echo(f"读取到 {len(df)} 条记录")
        
        # 检查必要的列 - 支持多种地址字段名
        address_fields = ['地址', 'street_address', 'address', 'Address', 'Street_Address']
        has_address_field = any(field in df.columns for field in address_fields)
        
        if not has_address_field:
            click.echo(f"错误: 缺少地址字段", err=True)
            click.echo("请确保CSV文件包含以下地址字段之一:")
            click.echo("- 地址 或 street_address 或 address (必需)")
            click.echo("- 收件人国家 (可选)")
            click.echo("- 收件人省/州 (可选)")
            click.echo("- 收件人城市 (可选)")
            click.echo("- 收件人邮编 (可选)")
            click.echo(f"\n当前文件包含的列: {', '.join(df.columns.tolist())}")
            sys.exit(1)
        
        # 显示列信息
        if verbose:
            click.echo("\n文件列信息:")
            for col in df.columns:
                click.echo(f"  - {col}")
        
        # 处理样本
        if sample and sample < len(df):
            df = df.head(sample)
            click.echo(f"处理样本: {len(df)} 条记录")
        
        # 初始化处理器
        click.echo("\n初始化处理器...")
        processor = IntegrationProcessor()
        
        # 处理数据
        click.echo("开始处理数据...")
        start_time = datetime.now()
        
        result_df = processor.process_dataframe(df)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # 保存结果
        click.echo(f"\n保存结果到: {output_file}")
        result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        # 显示统计信息
        stats = processor.get_stats()
        _display_processing_stats(stats, processing_time)
        
        # 生成处理报告
        if report:
            _generate_report(stats, processing_time, input_file, output_file, report)
            click.echo(f"处理报告已保存到: {report}")
        
        click.echo("\n✅ 处理完成！")
        
    except Exception as e:
        click.echo(f"处理失败: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--input', '-i', 'input_file', required=True, 
              help='输入CSV文件路径', type=click.Path(exists=True))
@click.option('--lines', '-n', default=5, help='显示行数', type=int)
def preview(input_file, lines):
    """预览CSV文件内容"""
    try:
        # 读取文件
        try:
            df = pd.read_csv(input_file, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(input_file, encoding='gbk')
            except UnicodeDecodeError:
                df = pd.read_csv(input_file, encoding='gb2312')
        
        click.echo(f"文件: {input_file}")
        click.echo(f"总行数: {len(df)}")
        click.echo(f"总列数: {len(df.columns)}")
        
        click.echo("\n列名:")
        for i, col in enumerate(df.columns, 1):
            click.echo(f"  {i}. {col}")
        
        click.echo(f"\n前 {lines} 行数据:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 50)
        
        preview_df = df.head(lines)
        click.echo(preview_df.to_string(index=False))
        
        # 检查地址格式
        if '地址' in df.columns:
            click.echo("\n地址格式示例:")
            for i, addr in enumerate(df['地址'].head(3), 1):
                if pd.notna(addr):
                    click.echo(f"  {i}. {addr}")
        
    except Exception as e:
        click.echo(f"预览失败: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--address', '-a', required=True, help='测试地址')
def test_single(address):
    """测试单个地址处理"""
    try:
        click.echo(f"测试地址: {address}")
        
        # 初始化处理器
        processor = IntegrationProcessor()
        
        # 构造测试数据
        test_data = {
            '地址': address,
            '收件人国家': 'United States',
            '收件人省/州': '',
            '收件人城市': '',
            '收件人邮编': ''
        }
        
        # 处理地址
        result = processor.process_single_address(test_data)
        
        # 显示结果
        click.echo("\n=== 处理结果 ===")
        
        # 现有规则结果
        click.echo("\n现有规则:")
        click.echo(f"  是否公寓: {result.get('是否公寓_原规则', False)}")
        click.echo(f"  置信度: {result.get('置信度_原规则', 0)}")
        click.echo(f"  匹配关键词: {result.get('匹配关键词_原规则', '')}")
        
        # Placekey增强结果
        if result.get('placekey_success'):
            click.echo("\nPlacekey增强:")
            click.echo(f"  Placekey: {result.get('placekey', '')}")
            click.echo(f"  API置信度: {result.get('placekey_confidence', '')}")
            click.echo(f"  公寓类型: {result.get('公寓类型_增强', '')}")
            click.echo(f"  主地址: {result.get('主地址_增强', '')}")
        else:
            click.echo("\nPlacekey增强: API调用失败或未配置")
        
        # 整合结果
        click.echo("\n最终整合结果:")
        click.echo(f"  是否公寓: {result.get('是否公寓_整合', False)}")
        click.echo(f"  置信度: {result.get('置信度_整合', 0)}")
        click.echo(f"  匹配关键词: {result.get('匹配关键词_整合', '')}")
        click.echo(f"  处理状态: {result.get('处理状态', '')}")
        click.echo(f"  冲突标记: {result.get('冲突标记', False)}")
        
    except Exception as e:
        click.echo(f"测试失败: {str(e)}", err=True)
        sys.exit(1)

@cli.command()
def validate_rules():
    """验证公寓识别规则"""
    try:
        from .integration_processor import ExistingApartmentClassifier
        
        classifier = ExistingApartmentClassifier()
        
        # 测试用例
        test_cases = [
            # 高置信度测试
            ("California~~~San Bernardino~~~Colton~~~2270 Cahuilla St Apt 154", True, 95),
            ("California~~~San Diego~~~San Diego~~~4340 44th St Apt 529", True, 95),
            ("California~~~Sacramento~~~Sacramento~~~6100 48th Ave Apt 5208", True, 95),
            ("California~~~Alameda~~~Oakland~~~1950 Broadway # 809", True, 60),
            ("California~~~Alameda~~~Hayward~~~659 Paradise Blvd apt B", True, 95),
            
            # 非公寓测试
            ("California~~~Los Angeles~~~Los Angeles~~~123 Main Street", False, 0),
            ("California~~~San Francisco~~~San Francisco~~~456 Oak Avenue", False, 0),
            
            # 边界情况
            ("California~~~Orange~~~Irvine~~~789 University Drive", False, 0),  # drive不是公寓
            ("California~~~San Diego~~~San Diego~~~321 North Street", False, 0),  # north在街道名中
        ]
        
        click.echo("=== 公寓识别规则验证 ===")
        
        passed = 0
        total = len(test_cases)
        
        for i, (address, expected_apt, expected_confidence) in enumerate(test_cases, 1):
            is_apt, confidence, keywords = classifier.classify_apartment(address)
            
            # 提取街道地址用于显示
            street_addr = classifier.extract_street_address(address)
            
            status = "✅" if (is_apt == expected_apt and 
                           (confidence >= 50) == expected_apt) else "❌"
            
            if status == "✅":
                passed += 1
            
            click.echo(f"\n{i}. {status} {street_addr}")
            click.echo(f"   预期: 公寓={expected_apt}, 置信度>={expected_confidence if expected_apt else 0}")
            click.echo(f"   实际: 公寓={is_apt}, 置信度={confidence}")
            if keywords:
                click.echo(f"   关键词: {keywords}")
        
        click.echo(f"\n=== 验证结果 ===")
        click.echo(f"通过: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if passed == total:
            click.echo("✅ 所有测试用例通过！")
        else:
            click.echo("❌ 部分测试用例失败，请检查规则实现")
        
    except Exception as e:
        click.echo(f"验证失败: {str(e)}", err=True)
        sys.exit(1)

def _display_processing_stats(stats: Dict[str, Any], processing_time: float):
    """显示处理统计信息"""
    total = stats['total_processed']
    if total == 0:
        return
    
    click.echo("\n=== 处理统计 ===")
    click.echo(f"总记录数: {total}")
    click.echo(f"处理时间: {processing_time:.2f}秒")
    click.echo(f"平均速度: {total/processing_time:.1f}条/秒")
    
    click.echo(f"\n现有规则匹配: {stats['existing_matches']} ({stats['existing_matches']/total*100:.1f}%)")
    click.echo(f"Placekey匹配: {stats['placekey_matches']} ({stats['placekey_matches']/total*100:.1f}%)")
    click.echo(f"双重匹配: {stats['both_matches']} ({stats['both_matches']/total*100:.1f}%)")
    click.echo(f"结果冲突: {stats['conflicts']} ({stats['conflicts']/total*100:.1f}%)")
    click.echo(f"API错误: {stats['api_errors']} ({stats['api_errors']/total*100:.1f}%)")

def _generate_report(stats: Dict[str, Any], processing_time: float, 
                    input_file: str, output_file: str, report_file: str):
    """生成处理报告"""
    report = {
        'processing_info': {
            'input_file': input_file,
            'output_file': output_file,
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat()
        },
        'statistics': stats,
        'summary': {
            'total_records': stats['total_processed'],
            'success_rate': (stats['total_processed'] - stats['api_errors']) / stats['total_processed'] * 100 if stats['total_processed'] > 0 else 0,
            'apartment_detection_rate': stats['existing_matches'] / stats['total_processed'] * 100 if stats['total_processed'] > 0 else 0,
            'placekey_enhancement_rate': stats['placekey_matches'] / stats['total_processed'] * 100 if stats['total_processed'] > 0 else 0,
            'conflict_rate': stats['conflicts'] / stats['total_processed'] * 100 if stats['total_processed'] > 0 else 0
        }
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

def process_csv_file(df, api_config=None):
    """
    处理CSV文件数据 - 修复版本，避免config重新加载问题
    
    Args:
        df: pandas DataFrame
        api_config: API配置字典，包含api_key和secret_key
    
    Returns:
        处理后的DataFrame
    """
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"API配置调试: api_config={api_config}")
        logger.debug(f"API配置类型: {type(api_config)}")
        
        # 直接传递API密钥给IntegrationProcessor，避免config重新加载
        api_key_to_use = api_config.get('api_key') if api_config else None
        logger.debug(f"提取的API密钥: {api_key_to_use[:10] + '...' if api_key_to_use else 'None'}")
        
        if api_key_to_use:
            logger.debug(f"使用提供的API密钥: {api_key_to_use[:10]}...")
        else:
            logger.warning("未提供API配置或API密钥为空，将使用默认配置")
        
        # 初始化处理器，直接传递API密钥
        processor = IntegrationProcessor(api_key=api_key_to_use)
        logger.debug("IntegrationProcessor初始化成功")
        
        # 处理数据
        logger.debug(f"开始处理DataFrame，形状: {df.shape}")
        result_df = processor.process_dataframe(df)
        logger.debug(f"处理完成，结果DataFrame形状: {result_df.shape}")
        
        return result_df
        
    except Exception as e:
        import traceback
        logger.error(f"处理CSV文件失败: {str(e)}")
        logger.error(f"错误堆栈: {traceback.format_exc()}")
        raise Exception(f"处理CSV文件失败: {str(e)}")

if __name__ == '__main__':
    cli()