#!/usr/bin/env python3
"""
Tag Analyzer for Obsidian Graph Visualization
Tracks tags, applies filters, and generates color-coded graph configurations
"""

import json
import colorsys
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import Counter
import math


class TagAnalyzer:
    def __init__(self, exclusions_file: str = None):
        self.tag_counts = Counter()
        self.conversation_tags = set()  # Track conversation grouping tags
        self.keyword_tags = set()       # Track keyword tags
        self.exclusions = self._load_exclusions(exclusions_file)
        
    def _load_exclusions(self, exclusions_file: str = None) -> Set[str]:
        """Load tag exclusions from file"""
        exclusions = set()
        
        if exclusions_file is None:
            # Use default exclusions file
            exclusions_file = Path(__file__).parent / 'tag_exclusions.txt'
        
        if Path(exclusions_file).exists():
            with open(exclusions_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        exclusions.add(line.lower())
        
        return exclusions
    
    def add_tag(self, tag: str, tag_type: str = 'keyword'):
        """Add a tag to the tracker"""
        if tag.startswith('#'):
            tag = tag[1:]  # Remove # prefix
        
        # Store the tag with its type
        if tag_type == 'conversation':
            self.conversation_tags.add(tag)
        else:
            self.keyword_tags.add(tag)
            
        self.tag_counts[tag] += 1
    
    def get_filtered_tags(self, min_count: int = 2) -> Dict[str, int]:
        """Get tags after applying exclusions and minimum count filter"""
        filtered = {}
        
        for tag, count in self.tag_counts.items():
            # Skip excluded tags (only for keyword tags, not conversation tags)
            if tag in self.keyword_tags and tag.lower() in self.exclusions:
                continue
            
            # Skip tags below minimum count
            if count < min_count:
                continue
                
            filtered[tag] = count
            
        return filtered
    
    def calculate_water_level(self, percentile: float = 0.95) -> int:
        """Calculate suggested water level based on tag distribution"""
        filtered_tags = self.get_filtered_tags(min_count=1)
        
        if not filtered_tags:
            return 1
            
        counts = sorted(filtered_tags.values())
        
        # Find the count at the given percentile
        index = int(len(counts) * (1 - percentile))
        if index >= len(counts):
            index = len(counts) - 1
            
        return counts[index] if index >= 0 else counts[0]
    
    def generate_color_groups(self, water_level: int = None, max_groups: int = 200) -> List[Dict]:
        """Generate color groups for Obsidian graph"""
        filtered_tags = self.get_filtered_tags()
        
        if water_level is None:
            water_level = self.calculate_water_level()
        
        # Filter by water level
        above_water = {tag: count for tag, count in filtered_tags.items() 
                      if count >= water_level}
        
        # Sort tags with conversation tags getting priority
        # First sort by count, then separate conversation tags
        sorted_tags = sorted(above_water.items(), key=lambda x: x[1], reverse=True)
        
        # Separate conversation tags and keyword tags
        conv_tags = [(tag, count) for tag, count in sorted_tags if tag in self.conversation_tags]
        keyword_tags = [(tag, count) for tag, count in sorted_tags if tag not in self.conversation_tags]
        
        # Combine with conversation tags first (they're unique per conversation)
        # Take top conversation tags and top keyword tags
        max_conv_tags = min(len(conv_tags), max_groups // 2)
        max_keyword_tags = max_groups - max_conv_tags
        
        sorted_tags = conv_tags[:max_conv_tags] + keyword_tags[:max_keyword_tags]
        
        # Limit to max groups
        sorted_tags = sorted_tags[:max_groups]
        
        # Generate colors using HSL
        color_groups = []
        for i, (tag, count) in enumerate(sorted_tags):
            # Use golden ratio for hue distribution
            hue = (i * 0.618033988749895) % 1.0
            
            # Vary saturation based on count (higher count = more saturated)
            max_count = sorted_tags[0][1] if sorted_tags else 1
            saturation = 0.4 + (count / max_count) * 0.4  # 0.4 to 0.8
            
            # Conversation tags get higher lightness
            if tag in self.conversation_tags:
                lightness = 0.6
            else:
                lightness = 0.5
            
            # Convert HSL to RGB
            rgb = self._hsl_to_rgb(hue, saturation, lightness)
            rgb_int = self._rgb_to_int(rgb)
            
            color_groups.append({
                "query": f"tag: #{tag}",
                "color": {
                    "a": 1,
                    "rgb": rgb_int
                }
            })
        
        return color_groups
    
    def _hsl_to_rgb(self, h: float, s: float, l: float) -> Tuple[int, int, int]:
        """Convert HSL to RGB"""
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def _rgb_to_int(self, rgb: Tuple[int, int, int]) -> int:
        """Convert RGB tuple to single integer (as Obsidian expects)"""
        r, g, b = rgb
        return (r << 16) | (g << 8) | b
    
    def create_obsidian_config(self, output_path: Path, water_level: int = None):
        """Create complete .obsidian directory with all config files"""
        # Create .obsidian directory
        obsidian_dir = output_path / '.obsidian'
        obsidian_dir.mkdir(exist_ok=True)
        
        # Copy all template files
        templates_dir = Path(__file__).parent / 'obsidian_templates'
        
        for template_file in templates_dir.glob('*.json'):
            target_file = obsidian_dir / template_file.name
            
            if template_file.name == 'graph.json':
                # Generate graph.json with color groups
                self._generate_graph_json(target_file, water_level)
            else:
                # Copy other files as-is
                import shutil
                shutil.copy2(template_file, target_file)
        
        return obsidian_dir
    
    def _generate_graph_json(self, graph_file: Path, water_level: int = None):
        """Generate graph.json with color groups"""
        # Load template
        template_file = Path(__file__).parent / 'obsidian_templates' / 'graph.json'
        with open(template_file, 'r') as f:
            graph_config = json.load(f)
        
        # Add color groups
        graph_config['colorGroups'] = self.generate_color_groups(water_level)
        
        # Write updated config
        with open(graph_file, 'w') as f:
            json.dump(graph_config, f, indent=2)
            
        return graph_file
    
    def get_tag_statistics(self) -> Dict:
        """Get statistics about the tags"""
        filtered_tags = self.get_filtered_tags()
        
        return {
            'total_unique_tags': len(self.tag_counts),
            'filtered_unique_tags': len(filtered_tags),
            'total_tag_occurrences': sum(self.tag_counts.values()),
            'filtered_tag_occurrences': sum(filtered_tags.values()),
            'conversation_tags': len(self.conversation_tags),
            'keyword_tags': len(self.keyword_tags),
            'excluded_tags': len(self.tag_counts) - len(filtered_tags),
            'suggested_water_level': self.calculate_water_level()
        }
    
    def interactive_water_level_adjustment(self) -> int:
        """Allow user to interactively adjust water level"""
        stats = self.get_tag_statistics()
        filtered_tags = self.get_filtered_tags()
        
        # Get count distribution
        if filtered_tags:
            counts = sorted(filtered_tags.values())
            min_count = counts[0]
            max_count = counts[-1]
            median_count = counts[len(counts) // 2]
        else:
            min_count = max_count = median_count = 0
        
        suggested_level = self.calculate_water_level()
        
        print("\n" + "="*60)
        print("TAG ANALYSIS COMPLETE")
        print("="*60)
        print(f"Total unique tags found: {stats['total_unique_tags']}")
        print(f"Tags after exclusion filter: {stats['filtered_unique_tags']}")
        print(f"Excluded common tags: {stats['excluded_tags']}")
        print(f"Conversation grouping tags: {stats['conversation_tags']}")
        print(f"Keyword tags: {stats['keyword_tags']}")
        print("\nTag frequency distribution:")
        print(f"  Minimum count: {min_count}")
        print(f"  Median count: {median_count}")
        print(f"  Maximum count: {max_count}")
        print(f"\nSuggested water level: {suggested_level}")
        tags_above_suggested = len([c for c in filtered_tags.values() if c >= suggested_level])
        print(f"Tags above water level: {tags_above_suggested}")
        
        # Recommend higher water level if too many tags
        if tags_above_suggested > 500:
            recommended_level = max(10, median_count)
            tags_at_recommended = len([c for c in filtered_tags.values() if c >= recommended_level])
            print(f"\n⚠️  WARNING: {tags_above_suggested} tags may slow down Obsidian!")
            print(f"Recommended water level: {recommended_level} (would show {tags_at_recommended} tags)")
        
        print("\nThe water level determines which tags appear in the graph.")
        print("Higher water level = fewer tags (only most frequent)")
        print("Lower water level = more tags (including less frequent)")
        print("\nFor best performance, keep total tags under 500.")
        
        while True:
            response = input(f"\nEnter water level (or press Enter for {suggested_level}): ").strip()
            
            if not response:
                return suggested_level
            
            try:
                level = int(response)
                if level < 1:
                    print("Water level must be at least 1")
                    continue
                    
                # Show how many tags this would include
                above_water = len([c for c in filtered_tags.values() if c >= level])
                print(f"This will include {above_water} tags in the graph")
                
                confirm = input("Use this water level? (y/N): ").strip().lower()
                if confirm == 'y':
                    return level
                    
            except ValueError:
                print("Please enter a valid number")
    
    def save_analysis_report(self, output_path: Path, water_level: int):
        """Save a detailed analysis report"""
        stats = self.get_tag_statistics()
        filtered_tags = self.get_filtered_tags()
        
        # Get tags above water level
        above_water = {tag: count for tag, count in filtered_tags.items() 
                      if count >= water_level}
        
        report = {
            'statistics': stats,
            'water_level_used': water_level,
            'tags_in_graph': len(above_water),
            'top_20_tags': dict(sorted(above_water.items(), 
                                     key=lambda x: x[1], 
                                     reverse=True)[:20]),
            'all_filtered_tags': dict(sorted(filtered_tags.items(), 
                                           key=lambda x: x[1], 
                                           reverse=True))
        }
        
        report_file = output_path / 'tag_analysis_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_file