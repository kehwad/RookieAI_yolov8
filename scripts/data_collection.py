#!/usr/bin/env python3
"""
游戏数据收集脚本
用于自动收集游戏截图作为训练数据

使用方法:
    python scripts/data_collection.py --game CS2 --duration 30 --fps 10
"""

import cv2
import numpy as np
import mss
import time
import os
import argparse
from datetime import datetime
import keyboard
import json
from pathlib import Path

class GameDataCollector:
    def __init__(self, game_name, duration_minutes=60, fps=10, output_dir="training_data"):
        self.game_name = game_name
        self.duration_minutes = duration_minutes
        self.fps = fps
        self.frame_interval = 1.0 / fps
        
        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.data_dir = Path(output_dir) / f"{game_name}_{timestamp}"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        self.stats = {
            "game_name": game_name,
            "start_time": datetime.now().isoformat(),
            "duration_minutes": duration_minutes,
            "target_fps": fps,
            "total_frames": 0,
            "avg_fps": 0,
            "data_dir": str(self.data_dir)
        }
        
    def collect_screenshots(self):
        """开始收集截图"""
        print(f"开始收集 {self.game_name} 的训练数据...")
        print(f"目标帧率: {self.fps} FPS")
        print(f"收集时长: {self.duration_minutes} 分钟")
        print(f"数据保存在: {self.data_dir}")
        print("按下 'q' 键或 'Esc' 键提前停止收集")
        print("3秒后开始收集...")
        
        for i in range(3, 0, -1):
            print(f"{i}...")
            time.sleep(1)
        print("开始收集！")
        
        with mss.mss() as sct:
            # 获取主显示器
            monitor = sct.monitors[1]
            
            start_time = time.time()
            frame_count = 0
            last_frame_time = 0
            
            while True:
                current_time = time.time()
                
                # 检查是否超时
                if (current_time - start_time) > (self.duration_minutes * 60):
                    print("\n收集时间到，停止收集")
                    break
                    
                # 检查按键停止
                if keyboard.is_pressed('q') or keyboard.is_pressed('esc'):
                    print("\n用户手动停止收集")
                    break
                
                # 控制帧率
                if current_time - last_frame_time < self.frame_interval:
                    time.sleep(0.001)  # 短暂休眠
                    continue
                    
                # 截取屏幕
                try:
                    screenshot = sct.grab(monitor)
                    img = np.array(screenshot)
                    img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
                    
                    # 保存图像
                    filename = self.data_dir / f"frame_{frame_count:06d}.jpg"
                    cv2.imwrite(str(filename), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
                    
                    frame_count += 1
                    last_frame_time = current_time
                    
                    # 每100帧显示进度
                    if frame_count % 100 == 0:
                        elapsed = current_time - start_time
                        current_fps = frame_count / elapsed if elapsed > 0 else 0
                        print(f"\r已收集 {frame_count} 张图片 | 当前FPS: {current_fps:.1f} | "
                              f"用时: {elapsed/60:.1f}分钟", end="", flush=True)
                        
                except Exception as e:
                    print(f"\n截图失败: {e}")
                    continue
            
            # 统计信息
            total_time = time.time() - start_time
            self.stats.update({
                "end_time": datetime.now().isoformat(),
                "total_frames": frame_count,
                "actual_duration": total_time / 60,
                "avg_fps": frame_count / total_time if total_time > 0 else 0
            })
            
            print(f"\n\n数据收集完成！")
            print(f"总共收集: {frame_count} 张图片")
            print(f"实际用时: {total_time/60:.1f} 分钟")
            print(f"平均FPS: {frame_count/total_time:.1f}")
            print(f"数据保存在: {self.data_dir}")
            
            # 保存统计信息
            self.save_stats()
            
    def save_stats(self):
        """保存收集统计信息"""
        stats_file = self.data_dir / "collection_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        print(f"统计信息已保存到: {stats_file}")
        
    def create_sample_preview(self, num_samples=9):
        """创建数据样本预览图"""
        image_files = list(self.data_dir.glob("*.jpg"))
        if len(image_files) < num_samples:
            print(f"图片数量不足，无法创建预览 (需要{num_samples}张，只有{len(image_files)}张)")
            return
            
        # 随机选择样本
        import random
        sample_files = random.sample(image_files, num_samples)
        
        # 创建拼接图
        images = []
        for img_file in sample_files:
            img = cv2.imread(str(img_file))
            if img is not None:
                # 缩放到统一大小
                img = cv2.resize(img, (320, 180))
                images.append(img)
                
        if len(images) == num_samples:
            # 3x3网格拼接
            rows = []
            for i in range(0, num_samples, 3):
                row = np.hstack(images[i:i+3])
                rows.append(row)
            preview = np.vstack(rows)
            
            preview_file = self.data_dir / "data_preview.jpg"
            cv2.imwrite(str(preview_file), preview)
            print(f"数据预览图已保存到: {preview_file}")

def main():
    parser = argparse.ArgumentParser(description="游戏数据收集工具")
    parser.add_argument("--game", required=True, help="游戏名称 (如: CS2, VALORANT, APEX)")
    parser.add_argument("--duration", type=int, default=30, help="收集时长（分钟），默认30分钟")
    parser.add_argument("--fps", type=int, default=10, help="目标帧率，默认10 FPS")
    parser.add_argument("--output", default="training_data", help="输出目录，默认为training_data")
    parser.add_argument("--preview", action="store_true", help="收集完成后创建数据预览")
    
    args = parser.parse_args()
    
    # 创建收集器并开始收集
    collector = GameDataCollector(
        game_name=args.game,
        duration_minutes=args.duration,
        fps=args.fps,
        output_dir=args.output
    )
    
    try:
        collector.collect_screenshots()
        
        if args.preview:
            collector.create_sample_preview()
            
    except KeyboardInterrupt:
        print("\n\n用户中断收集")
    except Exception as e:
        print(f"\n收集过程中出现错误: {e}")

if __name__ == "__main__":
    main()