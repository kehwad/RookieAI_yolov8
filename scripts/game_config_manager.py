#!/usr/bin/env python3
"""
游戏配置管理脚本
用于快速应用不同游戏的优化配置

使用方法:
    python scripts/game_config_manager.py --apply CS2
    python scripts/game_config_manager.py --list
    python scripts/game_config_manager.py --backup
"""

import argparse
import json
import shutil
from pathlib import Path
from datetime import datetime

# 导入项目配置模块
import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from Module.config import Config
    CONFIG_AVAILABLE = True
except ImportError:
    print("警告: 无法导入 Module.config，将使用独立模式")
    CONFIG_AVAILABLE = False

class GameConfigManager:
    """游戏配置管理器"""
    
    GAME_CONFIGS = {
        "CS2": {
            "display_name": "Counter-Strike 2",
            "confidence": 0.4,
            "aim_range": 200,
            "target_class": "0",
            "offset_centery": 0.85,
            "offset_centerx": 0.0,
            "screen_pixels_for_360_degrees": 6400,
            "screen_height_pixels": 3200,
            "aim_speed_x": 8.0,
            "aim_speed_y": 9.5,
            "near_speed_multiplier": 3.0,
            "slow_zone_radius": 15,
            "mouseMoveMode": "win32",
            "lockSpeed": 6.5,
            "jump_suppression_switch": True,
            "jump_suppression_fluctuation_range": 20,
            "description": "专为CS2优化的配置，提高精度减少误检"
        },
        
        "VALORANT": {
            "display_name": "VALORANT",
            "confidence": 0.35,
            "aim_range": 180,
            "target_class": "0",
            "offset_centery": 0.8,
            "offset_centerx": 0.0,
            "screen_pixels_for_360_degrees": 5800,
            "screen_height_pixels": 2900,
            "aim_speed_x": 7.2,
            "aim_speed_y": 8.8,
            "near_speed_multiplier": 2.8,
            "slow_zone_radius": 12,
            "mouseMoveMode": "KmBoxNet",
            "lockSpeed": 5.8,
            "jump_suppression_switch": True,
            "jump_suppression_fluctuation_range": 15,
            "description": "适配VALORANT反作弊的优化配置，推荐使用KmBoxNet"
        },
        
        "APEX": {
            "display_name": "Apex Legends",
            "confidence": 0.3,
            "aim_range": 250,
            "target_class": "0",
            "offset_centery": 0.75,
            "offset_centerx": 0.0,
            "screen_pixels_for_360_degrees": 6550,
            "screen_height_pixels": 3220,
            "aim_speed_x": 6.7,
            "aim_speed_y": 8.3,
            "near_speed_multiplier": 2.5,
            "slow_zone_radius": 10,
            "mouseMoveMode": "win32",
            "lockSpeed": 5.5,
            "jump_suppression_switch": False,
            "jump_suppression_fluctuation_range": 18,
            "description": "原始默认配置，适用于Apex Legends"
        },
        
        "COD": {
            "display_name": "Call of Duty",
            "confidence": 0.38,
            "aim_range": 220,
            "target_class": "0",
            "offset_centery": 0.82,
            "offset_centerx": 0.0,
            "screen_pixels_for_360_degrees": 7200,
            "screen_height_pixels": 3600,
            "aim_speed_x": 9.0,
            "aim_speed_y": 10.5,
            "near_speed_multiplier": 3.5,
            "slow_zone_radius": 18,
            "mouseMoveMode": "win32",
            "lockSpeed": 7.0,
            "jump_suppression_switch": True,
            "jump_suppression_fluctuation_range": 25,
            "description": "适用于使命召唤系列的高速度配置"
        },
        
        "PUBG": {
            "display_name": "PlayerUnknown's Battlegrounds",
            "confidence": 0.32,
            "aim_range": 300,
            "target_class": "0",
            "offset_centery": 0.78,
            "offset_centerx": 0.0,
            "screen_pixels_for_360_degrees": 5500,
            "screen_height_pixels": 2750,
            "aim_speed_x": 5.5,
            "aim_speed_y": 7.0,
            "near_speed_multiplier": 2.0,
            "slow_zone_radius": 25,
            "mouseMoveMode": "win32",
            "lockSpeed": 4.5,
            "jump_suppression_switch": False,
            "jump_suppression_fluctuation_range": 20,
            "description": "适用于PUBG的远距离精确配置"
        },
        
        "FORTNITE": {
            "display_name": "Fortnite",
            "confidence": 0.28,
            "aim_range": 280,
            "target_class": "0",
            "offset_centery": 0.73,
            "offset_centerx": 0.0,
            "screen_pixels_for_360_degrees": 6800,
            "screen_height_pixels": 3400,
            "aim_speed_x": 7.8,
            "aim_speed_y": 9.2,
            "near_speed_multiplier": 3.2,
            "slow_zone_radius": 20,
            "mouseMoveMode": "win32",
            "lockSpeed": 6.2,
            "jump_suppression_switch": True,
            "jump_suppression_fluctuation_range": 22,
            "description": "适用于Fortnite的快节奏配置"
        }
    }
    
    def __init__(self):
        self.backup_dir = Path("Data/config_backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    def list_games(self):
        """列出所有可用的游戏配置"""
        print("可用的游戏配置:\n")
        print(f"{'游戏代码':<12} {'游戏名称':<25} {'描述'}")
        print("-" * 80)
        
        for code, config in self.GAME_CONFIGS.items():
            print(f"{code:<12} {config['display_name']:<25} {config['description']}")
            
    def show_config(self, game_code):
        """显示指定游戏的详细配置"""
        if game_code not in self.GAME_CONFIGS:
            print(f"错误: 未找到游戏 '{game_code}' 的配置")
            return False
            
        config = self.GAME_CONFIGS[game_code]
        print(f"\n{config['display_name']} 配置详情:")
        print("=" * 50)
        
        # 排除非配置项
        exclude_keys = {'display_name', 'description'}
        for key, value in config.items():
            if key not in exclude_keys:
                print(f"{key:<35}: {value}")
                
        print(f"\n描述: {config['description']}")
        return True
        
    def backup_current_config(self):
        """备份当前配置"""
        if not CONFIG_AVAILABLE:
            print("错误: 无法访问配置系统进行备份")
            return False
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"config_backup_{timestamp}.json"
        
        try:
            current_config = Config.read()
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, indent=2, ensure_ascii=False)
            
            print(f"配置已备份到: {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            print(f"备份失败: {e}")
            return False
            
    def restore_config(self, backup_file):
        """从备份恢复配置"""
        if not CONFIG_AVAILABLE:
            print("错误: 无法访问配置系统进行恢复")
            return False
            
        backup_path = Path(backup_file)
        if not backup_path.exists():
            print(f"错误: 备份文件不存在: {backup_file}")
            return False
            
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_config = json.load(f)
                
            # 更新配置
            Config.content = backup_config
            Config.save()
            
            print(f"配置已从备份恢复: {backup_file}")
            return True
            
        except Exception as e:
            print(f"恢复失败: {e}")
            return False
            
    def apply_game_config(self, game_code, create_backup=True):
        """应用指定游戏的配置"""
        if game_code not in self.GAME_CONFIGS:
            print(f"错误: 未找到游戏 '{game_code}' 的配置")
            print("使用 --list 查看可用的游戏配置")
            return False
            
        if not CONFIG_AVAILABLE:
            print("错误: 无法访问配置系统")
            return False
            
        # 创建备份
        if create_backup:
            backup_file = self.backup_current_config()
            if backup_file:
                print(f"当前配置已备份")
                
        # 应用新配置
        config = self.GAME_CONFIGS[game_code]
        exclude_keys = {'display_name', 'description'}
        
        print(f"\n正在应用 {config['display_name']} 配置...")
        
        try:
            for key, value in config.items():
                if key not in exclude_keys:
                    Config.update(key, value)
                    print(f"  {key}: {value}")
                    
            print(f"\n✅ {config['display_name']} 配置应用完成!")
            print(f"描述: {config['description']}")
            return True
            
        except Exception as e:
            print(f"应用配置失败: {e}")
            return False
            
    def create_custom_config(self, game_code, base_config=None):
        """创建自定义游戏配置模板"""
        if base_config and base_config in self.GAME_CONFIGS:
            template = self.GAME_CONFIGS[base_config].copy()
            template['display_name'] = f"Custom {game_code}"
            template['description'] = f"基于 {self.GAME_CONFIGS[base_config]['display_name']} 的自定义配置"
        else:
            template = self.GAME_CONFIGS['APEX'].copy()  # 使用APEX作为默认模板
            template['display_name'] = f"Custom {game_code}"
            template['description'] = "自定义游戏配置"
            
        # 保存模板
        template_file = Path(f"custom_configs/{game_code.lower()}_template.json")
        template_file.parent.mkdir(exist_ok=True)
        
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
            
        print(f"自定义配置模板已创建: {template_file}")
        print("请编辑此文件以自定义您的配置")
        
    def list_backups(self):
        """列出所有备份文件"""
        backups = list(self.backup_dir.glob("config_backup_*.json"))
        
        if not backups:
            print("没有找到备份文件")
            return
            
        print("\n可用的配置备份:")
        print(f"{'文件名':<30} {'创建时间'}")
        print("-" * 50)
        
        for backup in sorted(backups, reverse=True):
            # 从文件名解析时间戳
            timestamp_str = backup.stem.replace("config_backup_", "")
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                time_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            except:
                time_str = "未知"
                
            print(f"{backup.name:<30} {time_str}")

def main():
    parser = argparse.ArgumentParser(description="游戏配置管理工具")
    parser.add_argument("--list", action="store_true", help="列出所有可用的游戏配置")
    parser.add_argument("--show", help="显示指定游戏的配置详情")
    parser.add_argument("--apply", help="应用指定游戏的配置")
    parser.add_argument("--backup", action="store_true", help="备份当前配置")
    parser.add_argument("--restore", help="从备份恢复配置")
    parser.add_argument("--list-backups", action="store_true", help="列出所有备份文件")
    parser.add_argument("--create-template", help="创建自定义配置模板")
    parser.add_argument("--base", help="创建模板时使用的基础配置")
    parser.add_argument("--no-backup", action="store_true", help="应用配置时不创建备份")
    
    args = parser.parse_args()
    
    manager = GameConfigManager()
    
    if args.list:
        manager.list_games()
        
    elif args.show:
        manager.show_config(args.show.upper())
        
    elif args.apply:
        create_backup = not args.no_backup
        success = manager.apply_game_config(args.apply.upper(), create_backup)
        if not success:
            sys.exit(1)
            
    elif args.backup:
        manager.backup_current_config()
        
    elif args.restore:
        success = manager.restore_config(args.restore)
        if not success:
            sys.exit(1)
            
    elif args.list_backups:
        manager.list_backups()
        
    elif args.create_template:
        manager.create_custom_config(args.create_template, args.base)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()