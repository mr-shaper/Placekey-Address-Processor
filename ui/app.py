#!/usr/bin/env python3
"""地址公寓识别与门禁码提取工具 - Web界面"""

import os
import sys
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import pandas as pd
from werkzeug.utils import secure_filename
import tempfile
import json
import glob
import shutil

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.apartment_accesscode.process_user_data import process_csv_file
from src.apartment_accesscode.placekey_client import PlacekeyClient
from src.apartment_accesscode.config import OUTPUT_DIR

app = Flask(__name__)
CORS(app)

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
app.logger.setLevel(logging.DEBUG)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
UPLOAD_FOLDER = tempfile.gettempdir()
OUTPUT_FOLDER = OUTPUT_DIR  # 使用配置文件中的输出路径

# 确保输出目录存在
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def cleanup_temp_files(max_age_hours=24):
    """清理临时文件和缓存
    
    Args:
        max_age_hours: 文件最大保留时间（小时），默认24小时
    """
    try:
        temp_dir = tempfile.gettempdir()
        current_time = datetime.now()
        deleted_count = 0
        
        # 定义要清理的文件模式
        patterns = [
            'upload_*.csv',
            'processed_*.csv',
            'temp_*.csv',
            'cache_*.csv'
        ]
        
        for pattern in patterns:
            file_pattern = os.path.join(temp_dir, pattern)
            files = glob.glob(file_pattern)
            
            for file_path in files:
                try:
                    # 检查文件修改时间
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    age_hours = (current_time - file_mtime).total_seconds() / 3600
                    
                    # 只删除超过指定时间的文件
                    if age_hours > max_age_hours:
                        # 验证文件路径安全性
                        if os.path.abspath(file_path).startswith(os.path.abspath(temp_dir)):
                            os.remove(file_path)
                            deleted_count += 1
                            app.logger.info(f'已删除过期文件: {file_path} (年龄: {age_hours:.1f}小时)')
                        else:
                            app.logger.warning(f'跳过不安全的文件路径: {file_path}')
                    else:
                        app.logger.debug(f'保留文件: {file_path} (年龄: {age_hours:.1f}小时)')
                        
                except Exception as e:
                    app.logger.warning(f'处理文件失败 {file_path}: {e}')
        
        app.logger.info(f'临时文件清理完成，删除了 {deleted_count} 个文件')
        return deleted_count
        
    except Exception as e:
        app.logger.error(f'清理临时文件时发生错误: {e}')
        return 0

def cleanup_old_files_on_startup():
    """启动时清理旧文件"""
    try:
        # 清理超过1小时的文件
        cleanup_temp_files(max_age_hours=1)
    except Exception as e:
        app.logger.error(f'启动时清理文件失败: {e}')

def cleanup_specific_file(filepath):
    """安全删除指定文件"""
    try:
        if os.path.exists(filepath):
            # 验证文件路径安全性
            temp_dir = tempfile.gettempdir()
            if os.path.abspath(filepath).startswith(os.path.abspath(temp_dir)):
                os.remove(filepath)
                app.logger.info(f'已删除文件: {filepath}')
                return True
            else:
                app.logger.warning(f'拒绝删除不安全的文件路径: {filepath}')
                return False
    except Exception as e:
        app.logger.error(f'删除文件失败 {filepath}: {e}')
        return False

# 启动时清理临时文件
cleanup_old_files_on_startup()

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        # 安全文件名处理
        original_filename = secure_filename(file.filename)
        if not original_filename:
            return jsonify({'success': False, 'error': '文件名无效'})
        
        if not original_filename.lower().endswith('.csv'):
            return jsonify({'success': False, 'error': '只支持CSV文件'})
        
        # 检查文件大小
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()
        file.seek(0)  # 重置到文件开头
        
        if file_size > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'success': False, 'error': f'文件大小超过限制({app.config["MAX_CONTENT_LENGTH"] // (1024*1024)}MB)'})
        
        if file_size == 0:
            return jsonify({'success': False, 'error': '文件为空'})
        
        # 生成安全的文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"upload_{timestamp}_{original_filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # 确保文件路径在允许的目录内
        if not os.path.abspath(filepath).startswith(os.path.abspath(UPLOAD_FOLDER)):
            return jsonify({'success': False, 'error': '文件路径无效'})
        
        # 保存文件
        file.save(filepath)
        app.logger.info(f'文件上传成功: {filepath}, 大小: {file_size} bytes')
        
        # 验证CSV文件格式
        try:
            df = pd.read_csv(filepath, nrows=0)  # 只读取表头验证格式
            if len(df.columns) == 0:
                os.remove(filepath)  # 删除无效文件
                return jsonify({'success': False, 'error': 'CSV文件格式无效：没有列'})
        except Exception as csv_error:
            if os.path.exists(filepath):
                os.remove(filepath)  # 删除无效文件
            return jsonify({'success': False, 'error': f'CSV文件格式无效: {str(csv_error)}'})
        
        # 读取CSV预览
        df = pd.read_csv(filepath)
        if len(df) == 0:
            return jsonify({'success': False, 'error': 'CSV文件没有数据行'})
        
        preview_rows = min(5, len(df))
        
        # 处理NaN值，将其转换为None或空字符串
        preview_df = df.head(preview_rows).fillna('')
        
        preview_data = {
            'headers': df.columns.tolist(),
            'rows': preview_df.values.tolist(),
            'total_rows': len(df)
        }
        
        return jsonify({
            'success': True,
            'filename': filename,
            'preview': preview_data,
            'total_rows': len(df)
        })
        
    except Exception as e:
        app.logger.error(f'文件上传失败: {e}')
        return jsonify({'success': False, 'error': f'上传失败: {str(e)}'})

@app.route('/api/process', methods=['POST'])
def process_file():
    try:
        data = request.get_json()
        
        # 获取已上传的文件名
        if 'filename' not in data:
            return jsonify({'success': False, 'error': '没有指定文件'})
        
        filename = secure_filename(data['filename'])
        if not filename:
            return jsonify({'success': False, 'error': '文件名无效'})
        
        # 确保文件名以upload_开头（安全检查）
        if not filename.startswith('upload_'):
            return jsonify({'success': False, 'error': '只能处理上传的文件'})
        
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # 验证文件路径在允许的目录内
        if not os.path.abspath(filepath).startswith(os.path.abspath(UPLOAD_FOLDER)):
            return jsonify({'success': False, 'error': '文件路径无效'})
        
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': '文件不存在，请重新上传'})
        
        # 获取列映射配置
        column_mapping = data.get('column_mapping', {})
        
        # 获取API配置
        api_config = data.get('api_config', {})
        
        app.logger.debug(f"收到API配置: {api_config}")
        
        # 生成安全的输出文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"processed_{timestamp}.csv"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # 验证输出路径安全性
        if not os.path.abspath(output_path).startswith(os.path.abspath(OUTPUT_FOLDER)):
            return jsonify({'success': False, 'error': '输出路径无效'})
        
        # 读取CSV文件
        try:
            df = pd.read_csv(filepath)
            if len(df) == 0:
                return jsonify({'success': False, 'error': '文件没有数据行'})
            app.logger.info(f"读取CSV文件成功，共{len(df)}行数据")
        except Exception as read_error:
            app.logger.error(f"读取CSV文件失败: {read_error}")
            return jsonify({'success': False, 'error': f'读取文件失败: {str(read_error)}'})
        
        # 处理文件
        try:
            app.logger.debug(f"开始处理CSV文件，使用API配置: {api_config}")
            processed_df = process_csv_file(df, api_config)
            app.logger.debug("CSV文件处理完成")
            
            if processed_df is None or len(processed_df) == 0:
                return jsonify({'success': False, 'error': '文件处理后没有数据'})
                
        except Exception as process_error:
            app.logger.error(f"处理文件时出错: {process_error}")
            return jsonify({'success': False, 'error': f'文件处理失败: {str(process_error)}'})
        
        # 保存处理后的文件
        try:
            processed_df.to_csv(output_path, index=False)
            app.logger.info(f"文件已保存到: {output_path}")
            
            # 验证文件是否真的被创建
            if not os.path.exists(output_path):
                raise Exception(f"文件保存失败，文件不存在: {output_path}")
            
            file_size = os.path.getsize(output_path)
            if file_size == 0:
                raise Exception("保存的文件为空")
                
            app.logger.info(f"保存的文件大小: {file_size} bytes")
            
        except Exception as save_error:
            app.logger.error(f"保存文件时出错: {save_error}")
            return jsonify({'success': False, 'error': f'保存处理结果失败: {str(save_error)}'})

        # 处理完成后清理旧的上传文件（保留当前文件）
        try:
            cleanup_temp_files(max_age_hours=1)
        except Exception as e:
            app.logger.warning(f'清理旧文件时出错: {e}')

        # 生成统计信息
        total_records = len(processed_df)
        
        # 计算公寓地址数量 - 检查是否公寓_整合字段
        apartment_count = 0
        if '是否公寓_整合' in processed_df.columns:
            apartment_count = len(processed_df[processed_df['是否公寓_整合'] == True])
        elif '是否公寓_原规则' in processed_df.columns:
            apartment_count = len(processed_df[processed_df['是否公寓_原规则'] == True])
        
        # 计算Placekey成功率
        placekey_success_count = 0
        if 'placekey_success' in processed_df.columns:
            placekey_success_count = len(processed_df[processed_df['placekey_success'] == True])
        
        stats = {
            'total_records': total_records,
            'total_processed': total_records,
            'apartment_count': apartment_count,
            'apartments_found': apartment_count,
            'placekey_success_count': placekey_success_count,
            'placekey_success_rate': (placekey_success_count / total_records * 100) if total_records > 0 else 0,
            'success_rate': 100.0
        }

        return jsonify({
            'success': True,
            'output_filename': output_filename,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/download/<filename>')
def download_file(filename):
    """下载处理后的文件"""
    try:
        # 安全文件名处理
        safe_filename = secure_filename(filename)
        if not safe_filename:
            return jsonify({'error': '无效的文件名'}), 400
        
        # 确保文件名以processed_开头（防止下载任意文件）
        if not safe_filename.startswith('processed_'):
            return jsonify({'error': '只能下载处理后的文件'}), 403
        
        filepath = os.path.join(OUTPUT_FOLDER, safe_filename)
        
        # 验证文件路径在允许的目录内
        if not os.path.abspath(filepath).startswith(os.path.abspath(OUTPUT_FOLDER)):
            return jsonify({'error': '文件路径无效'}), 403
        
        if os.path.exists(filepath):
            app.logger.info(f'下载文件: {filepath}')
            return send_file(filepath, as_attachment=True, download_name=safe_filename)
        else:
            app.logger.warning(f'请求的文件不存在: {filepath}')
            return jsonify({'error': '文件不存在'}), 404
            
    except Exception as e:
        app.logger.error(f'下载文件时发生错误: {e}')
        return jsonify({'error': '下载失败'}), 500

@app.route('/api/test-connection', methods=['POST'])
def test_api_connection():
    """测试API连接"""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        api_url = data.get('api_url')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API密钥不能为空'})
        
        # 创建测试客户端
        client = PlacekeyClient(api_key)
        
        # 发送测试请求
        test_address = {
            'street_address': '123 Main St',
            'city': 'New York',
            'state': 'NY',
            'postal_code': '10001'
        }
        
        try:
            result = client.get_placekey(test_address)
            if result and 'placekey' in result:
                return jsonify({'success': True, 'message': 'API连接成功'})
            else:
                return jsonify({'success': False, 'error': 'API返回格式异常'})
        except Exception as api_error:
            return jsonify({'success': False, 'error': f'API调用失败: {str(api_error)}'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download_template')
def download_template():
    """下载CSV模板文件"""
    try:
        return send_from_directory(
            directory=os.path.join(app.root_path, 'static'),
            path='template.csv',
            as_attachment=True,
            download_name='apartment_address_template.csv'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'下载模板失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)