#!/usr/bin/env python3
"""地址公寓识别与门禁码提取工具 - Web界面"""

import os
import sys
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import pandas as pd
from werkzeug.utils import secure_filename
import tempfile
import json
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.apartment_accesscode.process_user_data import process_csv_file
from src.apartment_accesscode.placekey_client import PlacekeyClient

app = Flask(__name__)
CORS(app)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
UPLOAD_FOLDER = tempfile.gettempdir()
OUTPUT_FOLDER = tempfile.gettempdir()

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
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'success': False, 'error': '只支持CSV文件'})
        
        # 保存上传的文件
        filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # 读取CSV预览
        df = pd.read_csv(filepath)
        preview_rows = min(5, len(df))
        
        preview_data = {
            'headers': df.columns.tolist(),
            'rows': df.head(preview_rows).values.tolist(),
            'total_rows': len(df)
        }
        
        return jsonify({
            'success': True,
            'filename': filename,
            'preview': preview_data,
            'total_rows': len(df)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/process', methods=['POST'])
def process_file():
    try:
        # 获取上传的文件
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'})
        
        # 获取列映射配置
        column_mapping = {}
        if 'column_mapping' in request.form:
            column_mapping = json.loads(request.form['column_mapping'])
        
        # 获取API配置
        api_config = {}
        if 'api_config' in request.form:
            api_config = json.loads(request.form['api_config'])
        
        # 保存临时文件
        temp_input = tempfile.NamedTemporaryFile(mode='w+b', suffix='.csv', delete=False)
        file.save(temp_input.name)
        temp_input.close()
        
        # 生成输出文件名
        output_filename = f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_path = os.path.join(OUTPUT_FOLDER, output_filename)
        
        # 处理文件
        stats = process_csv_file(temp_input.name, output_path, column_mapping, api_config)
        
        # 清理临时文件
        os.unlink(temp_input.name)
        
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
    filepath = os.path.join(OUTPUT_FOLDER, secure_filename(filename))
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': '文件不存在'}), 404

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
        client = PlacekeyClient(api_key, api_url)
        
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
            download_name='地址处理模板.csv'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'下载模板失败: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)