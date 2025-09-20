#!/usr/bin/env python3
"""
标注辅助脚本
用于验证和转换标注文件格式

使用方法:
    python scripts/annotation_helper.py --validate /path/to/annotations
    python scripts/annotation_helper.py --convert /path/to/xml /path/to/output
"""

import argparse
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import json
import shutil
from PIL import Image

class AnnotationHelper:
    """标注辅助工具"""
    
    def __init__(self):
        self.class_names = {
            0: "enemy",
            1: "teammate", 
            2: "enemy_head",
            3: "weapon",
            4: "explosive"
        }
        
    def validate_annotations(self, annotations_dir, images_dir=None):
        """验证标注文件的有效性"""
        annotations_path = Path(annotations_dir)
        
        if not annotations_path.exists():
            print(f"错误: 标注目录不存在: {annotations_dir}")
            return False
            
        # 统计信息
        stats = {
            "total_files": 0,
            "valid_files": 0,
            "empty_files": 0,
            "error_files": 0,
            "class_distribution": {},
            "errors": []
        }
        
        # 支持多种标注格式
        xml_files = list(annotations_path.glob("*.xml"))
        txt_files = list(annotations_path.glob("*.txt"))
        
        if xml_files:
            print(f"检测到 Pascal VOC 格式标注文件: {len(xml_files)} 个")
            self._validate_xml_annotations(xml_files, stats, images_dir)
        elif txt_files:
            print(f"检测到 YOLO 格式标注文件: {len(txt_files)} 个")
            self._validate_txt_annotations(txt_files, stats, images_dir)
        else:
            print("未找到支持的标注文件格式 (.xml 或 .txt)")
            return False
            
        # 显示统计结果
        self._show_validation_stats(stats)
        return stats["error_files"] == 0
        
    def _validate_xml_annotations(self, xml_files, stats, images_dir):
        """验证XML格式标注"""
        for xml_file in xml_files:
            stats["total_files"] += 1
            
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # 检查基本结构
                if root.find('filename') is None:
                    stats["errors"].append(f"{xml_file.name}: 缺少filename标签")
                    stats["error_files"] += 1
                    continue
                    
                # 检查对应的图片文件
                if images_dir:
                    img_name = root.find('filename').text
                    img_path = Path(images_dir) / img_name
                    if not img_path.exists():
                        stats["errors"].append(f"{xml_file.name}: 对应图片不存在: {img_name}")
                        
                # 检查标注对象
                objects = root.findall('object')
                if len(objects) == 0:
                    stats["empty_files"] += 1
                    stats["errors"].append(f"{xml_file.name}: 没有标注对象")
                    continue
                    
                # 统计类别分布
                for obj in objects:
                    class_name = obj.find('name').text
                    if class_name not in stats["class_distribution"]:
                        stats["class_distribution"][class_name] = 0
                    stats["class_distribution"][class_name] += 1
                    
                    # 验证边界框
                    bbox = obj.find('bndbox')
                    if bbox is not None:
                        try:
                            xmin = int(bbox.find('xmin').text)
                            ymin = int(bbox.find('ymin').text)
                            xmax = int(bbox.find('xmax').text)
                            ymax = int(bbox.find('ymax').text)
                            
                            if xmin >= xmax or ymin >= ymax:
                                stats["errors"].append(f"{xml_file.name}: 无效的边界框坐标")
                        except:
                            stats["errors"].append(f"{xml_file.name}: 边界框坐标格式错误")
                            
                stats["valid_files"] += 1
                
            except Exception as e:
                stats["error_files"] += 1
                stats["errors"].append(f"{xml_file.name}: 解析失败 - {str(e)}")
                
    def _validate_txt_annotations(self, txt_files, stats, images_dir):
        """验证YOLO格式标注"""
        for txt_file in txt_files:
            stats["total_files"] += 1
            
            try:
                # 检查对应的图片文件
                if images_dir:
                    img_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
                    img_found = False
                    for ext in img_extensions:
                        img_path = Path(images_dir) / (txt_file.stem + ext)
                        if img_path.exists():
                            img_found = True
                            break
                    if not img_found:
                        stats["errors"].append(f"{txt_file.name}: 未找到对应的图片文件")
                        
                with open(txt_file, 'r') as f:
                    lines = f.readlines()
                    
                if len(lines) == 0:
                    stats["empty_files"] += 1
                    continue
                    
                # 验证每一行
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    parts = line.split()
                    if len(parts) != 5:
                        stats["errors"].append(f"{txt_file.name}:{line_num}: 格式错误，应为5个数值")
                        continue
                        
                    try:
                        class_id = int(parts[0])
                        x_center, y_center, width, height = map(float, parts[1:5])
                        
                        # 验证范围
                        if not (0 <= x_center <= 1 and 0 <= y_center <= 1 and 
                               0 < width <= 1 and 0 < height <= 1):
                            stats["errors"].append(f"{txt_file.name}:{line_num}: 坐标超出范围 [0,1]")
                            
                        # 统计类别
                        class_name = self.class_names.get(class_id, f"class_{class_id}")
                        if class_name not in stats["class_distribution"]:
                            stats["class_distribution"][class_name] = 0
                        stats["class_distribution"][class_name] += 1
                        
                    except ValueError:
                        stats["errors"].append(f"{txt_file.name}:{line_num}: 数值格式错误")
                        
                stats["valid_files"] += 1
                
            except Exception as e:
                stats["error_files"] += 1
                stats["errors"].append(f"{txt_file.name}: 读取失败 - {str(e)}")
                
    def _show_validation_stats(self, stats):
        """显示验证统计结果"""
        print("\n" + "="*50)
        print("标注验证结果")
        print("="*50)
        print(f"总文件数: {stats['total_files']}")
        print(f"有效文件: {stats['valid_files']}")
        print(f"空文件: {stats['empty_files']}")
        print(f"错误文件: {stats['error_files']}")
        
        if stats["class_distribution"]:
            print("\n类别分布:")
            for class_name, count in stats["class_distribution"].items():
                print(f"  {class_name}: {count}")
                
        if stats["errors"]:
            print(f"\n错误详情 (显示前10个):")
            for error in stats["errors"][:10]:
                print(f"  - {error}")
            if len(stats["errors"]) > 10:
                print(f"  ... 还有 {len(stats['errors']) - 10} 个错误")
                
        # 给出建议
        if stats["error_files"] > 0:
            print("\n⚠️ 建议:")
            print("  - 修复上述错误后再进行训练")
            print("  - 检查标注文件格式是否正确")
        else:
            print("\n✅ 所有标注文件验证通过!")
            
    def convert_to_yolo_format(self, xml_dir, output_dir, class_mapping=None):
        """将Pascal VOC格式转换为YOLO格式"""
        xml_path = Path(xml_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if class_mapping is None:
            class_mapping = {"enemy": 0, "teammate": 1, "enemy_head": 2, "weapon": 3, "explosive": 4}
            
        xml_files = list(xml_path.glob("*.xml"))
        if not xml_files:
            print(f"在 {xml_dir} 中未找到XML文件")
            return False
            
        print(f"开始转换 {len(xml_files)} 个XML文件...")
        
        converted_count = 0
        error_count = 0
        
        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # 获取图片尺寸
                width = int(root.find('size/width').text)
                height = int(root.find('size/height').text)
                
                # 创建对应的txt文件
                txt_file = output_path / f"{xml_file.stem}.txt"
                
                with open(txt_file, 'w') as f:
                    for obj in root.findall('object'):
                        class_name = obj.find('name').text
                        
                        # 跳过未知类别
                        if class_name not in class_mapping:
                            print(f"警告: 跳过未知类别 '{class_name}' in {xml_file.name}")
                            continue
                            
                        class_id = class_mapping[class_name]
                        
                        # 获取边界框坐标
                        bbox = obj.find('bndbox')
                        xmin = int(bbox.find('xmin').text)
                        ymin = int(bbox.find('ymin').text)
                        xmax = int(bbox.find('xmax').text)
                        ymax = int(bbox.find('ymax').text)
                        
                        # 转换为YOLO格式 (归一化)
                        x_center = (xmin + xmax) / 2.0 / width
                        y_center = (ymin + ymax) / 2.0 / height
                        w = (xmax - xmin) / width
                        h = (ymax - ymin) / height
                        
                        f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
                        
                converted_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"转换失败: {xml_file.name} - {e}")
                
        print(f"\n转换完成:")
        print(f"  成功: {converted_count} 个文件")
        print(f"  失败: {error_count} 个文件")
        print(f"  输出目录: {output_path}")
        
        # 创建类别映射文件
        mapping_file = output_path / "classes.txt"
        with open(mapping_file, 'w') as f:
            for class_name, class_id in sorted(class_mapping.items(), key=lambda x: x[1]):
                f.write(f"{class_id}: {class_name}\n")
        print(f"  类别映射已保存到: {mapping_file}")
        
        return converted_count > 0
        
    def create_dataset_split(self, images_dir, labels_dir, output_dir, train_ratio=0.7, val_ratio=0.2):
        """创建数据集分割"""
        images_path = Path(images_dir)
        labels_path = Path(labels_dir)
        output_path = Path(output_dir)
        
        # 创建输出目录结构
        for subset in ['train', 'val', 'test']:
            (output_path / 'images' / subset).mkdir(parents=True, exist_ok=True)
            (output_path / 'labels' / subset).mkdir(parents=True, exist_ok=True)
            
        # 获取所有图片文件
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(images_path.glob(ext))
            
        if not image_files:
            print(f"在 {images_dir} 中未找到图片文件")
            return False
            
        # 随机打乱
        import random
        random.shuffle(image_files)
        
        # 计算分割点
        total = len(image_files)
        train_end = int(total * train_ratio)
        val_end = int(total * (train_ratio + val_ratio))
        
        splits = {
            'train': image_files[:train_end],
            'val': image_files[train_end:val_end],
            'test': image_files[val_end:]
        }
        
        print(f"数据集分割:")
        for subset, files in splits.items():
            print(f"  {subset}: {len(files)} 个文件")
            
            # 复制文件
            for img_file in files:
                # 复制图片
                dst_img = output_path / 'images' / subset / img_file.name
                shutil.copy2(img_file, dst_img)
                
                # 复制对应的标注文件
                label_file = labels_path / (img_file.stem + '.txt')
                if label_file.exists():
                    dst_label = output_path / 'labels' / subset / label_file.name
                    shutil.copy2(label_file, dst_label)
                else:
                    print(f"警告: 未找到标注文件 {label_file.name}")
                    
        # 创建data.yaml
        self.create_data_yaml(output_path, list(self.class_names.values()))
        print(f"\n数据集已创建: {output_path}")
        return True
        
    def create_data_yaml(self, dataset_path, class_names):
        """创建data.yaml配置文件"""
        data_yaml_content = f"""path: {dataset_path.absolute()}
train: images/train
val: images/val
test: images/test

# Classes
nc: {len(class_names)}
names: {class_names}
"""
        
        yaml_file = dataset_path / "data.yaml"
        with open(yaml_file, 'w', encoding='utf-8') as f:
            f.write(data_yaml_content)
        print(f"data.yaml 已创建: {yaml_file}")

def main():
    parser = argparse.ArgumentParser(description="标注辅助工具")
    parser.add_argument("--validate", help="验证标注文件")
    parser.add_argument("--images", help="对应的图片目录 (验证时可选)")
    parser.add_argument("--convert", nargs=2, metavar=('XML_DIR', 'OUTPUT_DIR'), 
                       help="转换Pascal VOC到YOLO格式")
    parser.add_argument("--split", nargs=3, metavar=('IMAGES_DIR', 'LABELS_DIR', 'OUTPUT_DIR'),
                       help="创建数据集分割")
    parser.add_argument("--train-ratio", type=float, default=0.7, help="训练集比例")
    parser.add_argument("--val-ratio", type=float, default=0.2, help="验证集比例")
    
    args = parser.parse_args()
    
    helper = AnnotationHelper()
    
    if args.validate:
        success = helper.validate_annotations(args.validate, args.images)
        if not success:
            sys.exit(1)
            
    elif args.convert:
        xml_dir, output_dir = args.convert
        success = helper.convert_to_yolo_format(xml_dir, output_dir)
        if not success:
            sys.exit(1)
            
    elif args.split:
        images_dir, labels_dir, output_dir = args.split
        success = helper.create_dataset_split(
            images_dir, labels_dir, output_dir, 
            args.train_ratio, args.val_ratio
        )
        if not success:
            sys.exit(1)
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main()