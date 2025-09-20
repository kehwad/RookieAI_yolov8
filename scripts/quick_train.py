#!/usr/bin/env python3
"""
快速模型训练脚本
简化的模型训练工具，适合初学者使用

使用方法:
    python scripts/quick_train.py --game CS2 --data /path/to/dataset --epochs 200
"""

import argparse
import os
import sys
import torch
from pathlib import Path
from datetime import datetime

# 检查 ultralytics 是否可用
try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    print("错误: 未安装 ultralytics")
    print("请运行: poetry run pip install ultralytics")
    sys.exit(1)

class QuickTrainer:
    """快速训练器"""
    
    def __init__(self, game_name, data_path, output_dir="models"):
        self.game_name = game_name
        self.data_path = Path(data_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 验证数据路径
        if not self.data_path.exists():
            raise FileNotFoundError(f"数据集路径不存在: {data_path}")
            
        # 检查数据集结构
        self.validate_dataset()
        
    def validate_dataset(self):
        """验证数据集结构"""
        required_dirs = ['images/train', 'images/val', 'labels/train', 'labels/val']
        missing_dirs = []
        
        for dir_path in required_dirs:
            if not (self.data_path / dir_path).exists():
                missing_dirs.append(dir_path)
                
        if missing_dirs:
            print("警告: 缺少以下目录:")
            for dir_path in missing_dirs:
                print(f"  - {dir_path}")
            print("请确保数据集按照YOLO格式组织")
            
        # 检查 data.yaml 文件
        data_yaml = self.data_path / "data.yaml"
        if not data_yaml.exists():
            print("警告: 未找到 data.yaml 文件")
            self.create_data_yaml()
            
    def create_data_yaml(self):
        """创建基本的 data.yaml 文件"""
        data_yaml_content = f"""path: {self.data_path.absolute()}
train: images/train
val: images/val
test: images/test  # 可选

# 类别定义 (请根据实际情况修改)
nc: 1  # 类别数量
names: 
  0: enemy  # 敌人
"""
        
        data_yaml_path = self.data_path / "data.yaml"
        with open(data_yaml_path, 'w', encoding='utf-8') as f:
            f.write(data_yaml_content)
            
        print(f"已创建基础 data.yaml 文件: {data_yaml_path}")
        print("请根据您的实际类别修改此文件")
        
    def get_recommended_params(self, model_size):
        """根据模型大小获取推荐参数"""
        params = {
            'yolov8n': {
                'batch': 16,
                'imgsz': 640,
                'lr0': 0.01,
                'description': '最快的模型，适合快速测试'
            },
            'yolov8s': {
                'batch': 12,
                'imgsz': 640,
                'lr0': 0.01,
                'description': '小型模型，平衡速度和精度'
            },
            'yolov8m': {
                'batch': 8,
                'imgsz': 640,
                'lr0': 0.01,
                'description': '中型模型，更高精度'
            },
            'yolov8l': {
                'batch': 4,
                'imgsz': 640,
                'lr0': 0.01,
                'description': '大型模型，最高精度但速度较慢'
            }
        }
        
        return params.get(model_size, params['yolov8n'])
        
    def train_model(self, model_size='yolov8n', epochs=200, batch_size=None, 
                   img_size=640, use_pretrained=True, device='auto'):
        """训练模型"""
        
        print(f"开始训练 {self.game_name} 模型")
        print(f"模型: {model_size}")
        print(f"数据集: {self.data_path}")
        print(f"训练轮数: {epochs}")
        
        # 获取推荐参数
        recommended = self.get_recommended_params(model_size)
        if batch_size is None:
            batch_size = recommended['batch']
            
        print(f"批处理大小: {batch_size}")
        print(f"图片尺寸: {img_size}")
        print(f"模型说明: {recommended['description']}")
        
        # 检查GPU
        if device == 'auto':
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"训练设备: {device}")
        
        if device == 'cpu':
            print("警告: 使用CPU训练将非常缓慢，建议使用GPU")
            
        # 加载模型
        if use_pretrained:
            model_path = f"{model_size}.pt"
            print(f"使用预训练模型: {model_path}")
        else:
            model_path = f"{model_size}.yaml"
            print(f"从头开始训练: {model_path}")
            
        try:
            model = YOLO(model_path)
        except Exception as e:
            print(f"加载模型失败: {e}")
            return False
            
        # 创建运行目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_name = f"{self.game_name}_{model_size}_{timestamp}"
        
        # 训练参数
        train_args = {
            'data': str(self.data_path / 'data.yaml'),
            'epochs': epochs,
            'batch': batch_size,
            'imgsz': img_size,
            'device': device,
            'project': str(self.output_dir),
            'name': run_name,
            'save': True,
            'save_period': max(10, epochs // 10),  # 每10轮或10%轮数保存一次
            'val': True,
            'plots': True,
            'verbose': True,
            
            # 数据增强 (适中的设置)
            'hsv_h': 0.015,
            'hsv_s': 0.7,
            'hsv_v': 0.4,
            'degrees': 0.0,
            'translate': 0.1,
            'scale': 0.5,
            'shear': 0.0,
            'perspective': 0.0,
            'flipud': 0.0,
            'fliplr': 0.5,
            'mosaic': 1.0,
            'mixup': 0.0,
            
            # 优化器
            'optimizer': 'SGD',
            'lr0': recommended['lr0'],
            'lrf': 0.1,
            'momentum': 0.937,
            'weight_decay': 0.0005,
            'warmup_epochs': 3,
            'warmup_momentum': 0.8,
            'warmup_bias_lr': 0.1,
            
            # 其他
            'cos_lr': True,
            'close_mosaic': 10,
            'resume': False,
            'amp': True,
            'patience': max(30, epochs // 10),  # 早停
        }
        
        print("\n开始训练...")
        print("=" * 50)
        
        try:
            # 开始训练
            results = model.train(**train_args)
            
            # 训练完成后处理
            best_model_path = self.output_dir / run_name / "weights" / "best.pt"
            final_model_path = self.output_dir / f"{self.game_name}_{model_size}.pt"
            
            # 复制最佳模型
            if best_model_path.exists():
                import shutil
                shutil.copy2(best_model_path, final_model_path)
                print(f"\n✅ 训练完成!")
                print(f"最佳模型已保存到: {final_model_path}")
                print(f"训练详细结果在: {self.output_dir / run_name}")
                
                # 显示训练结果摘要
                self.show_training_summary(results, final_model_path)
                return str(final_model_path)
            else:
                print("⚠️ 训练完成但未找到最佳模型文件")
                return False
                
        except KeyboardInterrupt:
            print("\n\n用户中断训练")
            return False
        except Exception as e:
            print(f"\n训练过程中出现错误: {e}")
            return False
            
    def show_training_summary(self, results, model_path):
        """显示训练结果摘要"""
        print("\n" + "="*50)
        print("训练结果摘要")
        print("="*50)
        
        try:
            # 基本信息
            print(f"模型路径: {model_path}")
            print(f"模型大小: {model_path.stat().st_size / 1024 / 1024:.1f} MB")
            
            # 如果有结果数据
            if hasattr(results, 'results_dict'):
                metrics = results.results_dict
                if 'metrics/mAP50(B)' in metrics:
                    print(f"最佳 mAP@0.5: {metrics['metrics/mAP50(B)']:.3f}")
                if 'metrics/mAP50-95(B)' in metrics:
                    print(f"最佳 mAP@0.5:0.95: {metrics['metrics/mAP50-95(B)']:.3f}")
                    
        except Exception as e:
            print(f"无法显示详细结果: {e}")
            
        print("\n下一步:")
        print("1. 使用 Tools/PT_to_TRT.py 转换模型以提高推理速度")
        print("2. 使用游戏配置管理器应用对应游戏的配置")
        print("3. 在游戏中测试模型效果")
        
    def quick_benchmark(self, model_path):
        """快速性能测试"""
        import time
        import numpy as np
        
        print(f"\n正在测试模型性能: {model_path}")
        
        try:
            model = YOLO(model_path)
            
            # 创建测试图像
            test_img = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            
            # 预热
            for _ in range(5):
                model.predict(test_img, verbose=False)
                
            # 性能测试
            times = []
            for _ in range(50):
                start = time.time()
                results = model.predict(test_img, verbose=False)
                end = time.time()
                times.append(end - start)
                
            avg_time = np.mean(times) * 1000  # 转换为毫秒
            fps = 1000 / avg_time
            
            print(f"平均推理时间: {avg_time:.2f}ms")
            print(f"推理帧率: {fps:.1f} FPS")
            
            if fps >= 60:
                print("✅ 性能优秀，适合实时应用")
            elif fps >= 30:
                print("✅ 性能良好，可以使用")
            else:
                print("⚠️ 性能较低，建议优化或使用更小的模型")
                
        except Exception as e:
            print(f"性能测试失败: {e}")

def main():
    parser = argparse.ArgumentParser(description="快速模型训练工具")
    parser.add_argument("--game", required=True, help="游戏名称")
    parser.add_argument("--data", required=True, help="数据集路径")
    parser.add_argument("--model", choices=['yolov8n', 'yolov8s', 'yolov8m', 'yolov8l'], 
                       default='yolov8n', help="模型大小")
    parser.add_argument("--epochs", type=int, default=200, help="训练轮数")
    parser.add_argument("--batch", type=int, help="批处理大小 (自动根据模型推荐)")
    parser.add_argument("--imgsz", type=int, default=640, help="输入图片尺寸")
    parser.add_argument("--device", default='auto', help="训练设备 (auto/cpu/cuda)")
    parser.add_argument("--no-pretrained", action="store_true", help="不使用预训练模型")
    parser.add_argument("--output", default="models", help="输出目录")
    parser.add_argument("--benchmark", action="store_true", help="训练完成后进行性能测试")
    
    args = parser.parse_args()
    
    try:
        # 创建训练器
        trainer = QuickTrainer(args.game, args.data, args.output)
        
        # 开始训练
        model_path = trainer.train_model(
            model_size=args.model,
            epochs=args.epochs,
            batch_size=args.batch,
            img_size=args.imgsz,
            use_pretrained=not args.no_pretrained,
            device=args.device
        )
        
        # 性能测试
        if args.benchmark and model_path:
            trainer.quick_benchmark(model_path)
            
    except KeyboardInterrupt:
        print("\n用户中断程序")
        sys.exit(1)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()