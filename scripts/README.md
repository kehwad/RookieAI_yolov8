# 脚本使用说明

本目录包含了用于训练其他游戏模型的实用脚本工具。

## 脚本列表

### 1. data_collection.py - 数据收集脚本
自动收集游戏截图作为训练数据。

**使用示例:**
```bash
# 收集CS2游戏数据，持续30分钟，10 FPS
python scripts/data_collection.py --game CS2 --duration 30 --fps 10 --preview

# 自定义输出目录
python scripts/data_collection.py --game VALORANT --duration 60 --output my_training_data
```

**参数说明:**
- `--game`: 游戏名称（必需）
- `--duration`: 收集时长（分钟），默认30分钟
- `--fps`: 目标帧率，默认10 FPS
- `--output`: 输出目录，默认为training_data
- `--preview`: 收集完成后创建数据预览图

**注意事项:**
- 运行前确保游戏已启动并处于全屏状态
- 按 'q' 或 'Esc' 键可以提前停止收集
- 建议收集多种场景的数据以提高模型泛化能力

### 2. game_config_manager.py - 游戏配置管理脚本
管理不同游戏的配置参数。

**使用示例:**
```bash
# 列出所有可用的游戏配置
python scripts/game_config_manager.py --list

# 显示CS2的配置详情
python scripts/game_config_manager.py --show CS2

# 应用VALORANT配置
python scripts/game_config_manager.py --apply VALORANT

# 备份当前配置
python scripts/game_config_manager.py --backup

# 从备份恢复配置
python scripts/game_config_manager.py --restore Data/config_backups/config_backup_20241228_123456.json
```

**支持的游戏:**
- CS2 (Counter-Strike 2)
- VALORANT
- APEX (Apex Legends)
- COD (Call of Duty)
- PUBG
- FORTNITE

### 3. quick_train.py - 快速模型训练脚本
简化的模型训练工具，适合初学者使用。

**使用示例:**
```bash
# 基本训练
python scripts/quick_train.py --game CS2 --data /path/to/dataset --epochs 200

# 使用不同模型大小和参数
python scripts/quick_train.py --game VALORANT --data ./dataset --model yolov8s --epochs 300 --batch 8

# 训练完成后进行性能测试
python scripts/quick_train.py --game APEX --data ./dataset --benchmark
```

**参数说明:**
- `--game`: 游戏名称（必需）
- `--data`: 数据集路径（必需）
- `--model`: 模型大小（yolov8n/s/m/l），默认yolov8n
- `--epochs`: 训练轮数，默认200
- `--batch`: 批处理大小，默认自动推荐
- `--device`: 训练设备（auto/cpu/cuda）
- `--benchmark`: 训练完成后进行性能测试

### 4. annotation_helper.py - 标注辅助脚本
用于验证和转换标注文件格式。

**使用示例:**
```bash
# 验证标注文件
python scripts/annotation_helper.py --validate /path/to/annotations --images /path/to/images

# 转换Pascal VOC格式到YOLO格式
python scripts/annotation_helper.py --convert /path/to/xml /path/to/output

# 创建数据集分割
python scripts/annotation_helper.py --split /path/to/images /path/to/labels /path/to/dataset
```

**功能:**
- 验证标注文件的有效性
- 支持XML (Pascal VOC) 和TXT (YOLO) 格式
- 自动转换标注格式
- 创建训练/验证/测试数据集分割

## 完整工作流程示例

以下是训练CS2模型的完整流程：

### 1. 数据收集
```bash
# 收集CS2游戏数据
python scripts/data_collection.py --game CS2 --duration 60 --fps 8 --preview
```

### 2. 数据标注
使用LabelImg进行标注：
```bash
# 安装LabelImg
poetry run pip install labelImg

# 启动标注工具
poetry run labelImg
```

### 3. 验证和处理标注
```bash
# 验证标注质量
python scripts/annotation_helper.py --validate /path/to/annotations --images /path/to/images

# 如果是XML格式，转换为YOLO格式
python scripts/annotation_helper.py --convert /path/to/xml /path/to/yolo_labels

# 创建数据集分割
python scripts/annotation_helper.py --split /path/to/images /path/to/labels /path/to/final_dataset
```

### 4. 训练模型
```bash
# 开始训练
python scripts/quick_train.py --game CS2 --data /path/to/final_dataset --epochs 300 --benchmark
```

### 5. 优化模型
```bash
# 转换为TensorRT格式以提升性能
python Tools/PT_to_TRT.py
```

### 6. 应用配置
```bash
# 应用CS2专用配置
python scripts/game_config_manager.py --apply CS2
```

### 7. 测试模型
启动RookieAI.py并在游戏中测试效果。

## 常见问题

### Q: 数据收集时帧率很低怎么办？
A: 降低FPS参数，如 `--fps 5` 或 `--fps 2`。

### Q: 训练时出现CUDA内存不足？
A: 减小批处理大小，如 `--batch 4` 或 `--batch 2`。

### Q: 模型精度不够高？
A: 
- 增加训练数据量
- 提高训练轮数
- 使用更大的模型 (`--model yolov8s` 或 `yolov8m`)
- 改善数据标注质量

### Q: 推理速度太慢？
A: 
- 使用更小的模型 (`yolov8n`)
- 转换为TensorRT格式
- 降低输入图片尺寸

## 技术支持

如果遇到问题，请：
1. 查看控制台输出的错误信息
2. 检查数据集格式是否正确
3. 确认环境依赖是否完整安装
4. 参考项目主README中的Discord社区链接获取帮助

## 免责声明

这些脚本仅供学习和研究目的，使用时请遵守相关游戏的服务条款和当地法律法规。