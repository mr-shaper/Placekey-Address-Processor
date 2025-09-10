# 地址处理器使用示例

## 基本使用

```python
from apartment_classifier.address_processor import AddressProcessor

# 初始化处理器
processor = AddressProcessor()

# 测试地址
address = {
    'street_address': '2270 Cahuilla St Apt 154',
    'city': 'Palm Springs',
    'region': 'CA',
    'postal_code': '92262',
    'iso_country_code': 'US'
}

# 使用精度优化（推荐）
result = processor.process_address(address, use_precision_optimization=True)

if result['placekey_result']['success']:
    placekey_data = result['placekey_result']
    print(f"Placekey: {placekey_data['placekey']}")
    print(f"精度评分: {placekey_data['precision_score']}/100")
    print(f"使用策略: {placekey_data['strategy_name']}")
    print(f"位置类型: {placekey_data['location_type']}")
else:
    print(f"处理失败: {result['placekey_result']['error']}")
```

## 精度优化功能

### 多策略测试
改进后的处理器会自动测试多种地址格式：
1. **原始地址** - 保持用户输入的完整格式
2. **移除公寓号** - 去除单元/公寓信息，获取建筑物级别定位
3. **标准化地址** - 应用地址标准化规则
4. **简化地址** - 仅使用核心地址信息

### 精度评分系统
- **100分**: 屋顶级别精度 (ROOFTOP)
- **80分**: 范围插值精度 (RANGE_INTERPOLATED)
- **65分**: 近似精度 (APPROXIMATE)
- **50分**: 几何中心精度 (GEOMETRIC_CENTER)

### 精度分析报告
```python
if 'precision_analysis' in result['placekey_result']:
    analysis = result['placekey_result']['precision_analysis']
    
    print(f"测试策略数: {analysis['strategies_tested']}")
    print(f"成功策略数: {analysis['successful_strategies']}")
    
    print("\n精度说明:")
    for note in analysis['precision_notes']:
        print(f"- {note}")
    
    print("\n所有策略结果:")
    for result in analysis['all_results']:
        print(f"- {result['strategy_name']}: {result['precision_score']}/100")
```

## 常见问题解答

### Q: 为什么门牌号从2270变成了2260？
A: 这是由于地址插值造成的。当数据库中没有精确的GPS记录时，系统会基于已知的地址范围进行插值计算，可能导致门牌号略有偏差。

### Q: 什么是RANGE_INTERPOLATED？
A: 这表示坐标是通过范围插值计算得出的，而不是基于精确的GPS记录。这种情况下，位置精度可能存在一定偏差。

### Q: 如何提高地址定位精度？
A: 
1. 使用 `use_precision_optimization=True` 参数
2. 提供完整准确的地址信息
3. 检查精度评分，选择评分最高的结果
4. 对于重要应用，考虑使用多个地理编码服务进行交叉验证

### Q: 不同策略产生不同Placekey正常吗？
A: 是的，这是正常现象。不同的地址格式可能匹配到不同的地理位置记录，从而产生不同的Placekey。系统会自动选择精度评分最高的结果。

## 最佳实践

1. **总是使用精度优化**: 设置 `use_precision_optimization=True`
2. **检查精度评分**: 评分低于80的结果需要特别注意
3. **阅读精度说明**: 了解定位结果的可靠程度
4. **保留原始地址**: 用于后续验证和调试
5. **记录处理结果**: 包括使用的策略和精度评分

## 示例输出

```
=== 精度优化结果 ===
Placekey: 0f7yr4uck2@5z6-9d8-t7q
精度评分: 80.0/100
使用策略: 原始地址
位置类型: RANGE_INTERPOLATED

精度分析:
- 测试了3种不同的地址格式策略
- 该地址在数据库中没有精确的GPS记录
- 这可能导致门牌号与实际位置存在偏差（如2270变成2260）
- 不同地址格式产生了2个不同的Placekey
- 已选择精度评分最高的结果
```

这个改进版本帮助用户更好地理解地址定位的复杂性，并提供了解决精度问题的实用工具。