#!/usr/bin/env python3
"""
Tag Analyzer for Obsidian Graph Visualization
Tracks tags, applies filters, and generates color-coded graph configurations
"""

import json
import colorsys
import shutil
import re
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
        self.file_patterns = Counter()  # Track file name patterns
        self.file_to_pattern = {}       # Map files to their patterns
        
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
        """Calculate water level based on log distribution of tag counts"""
        filtered_tags = self.get_filtered_tags(min_count=1)
        
        if not filtered_tags:
            return 30  # Default to 30
            
        counts = sorted(filtered_tags.values(), reverse=True)
        
        # For log distribution, we want to find a natural break point
        # where the rate of change in counts decreases significantly
        
        if len(counts) < 10:
            return max(2, counts[len(counts)//2])
        
        # Calculate log-based threshold
        # We want to capture the "head" of the distribution
        max_count = counts[0]
        min_count = counts[-1]
        
        if max_count <= 30:
            # If max is already <= 30, use a lower threshold
            return max(2, int(max_count * 0.3))
        
        # Use log scale to find natural cutoff
        # log(max) to log(30) represents the meaningful range
        log_max = math.log(max_count)
        log_threshold = math.log(30)  # Our target is around 30
        
        # Find the count closest to our log threshold
        for count in counts:
            if count <= 30:
                return 30
        
        # Default to 30 as it's a good balance
        return 30
    
    def _calculate_bayesian_score(self, term: str, count: int, total_terms: int, 
                                 doc_freq: int = None, total_docs: int = None,
                                 is_file_pattern: bool = False) -> float:
        """Calculate Bayesian-weighted relevance score for a term"""
        # Basic term frequency
        tf = count / total_terms if total_terms > 0 else 0
        
        # Prior probability based on term characteristics
        prior = 1.0
        
        # Boost conversation tags slightly
        if term.startswith('conv-'):
            prior *= 1.2
            
        # For file patterns, prefer single words (they're already simplified)
        if is_file_pattern:
            # Single word patterns are good - they group broadly
            prior *= 1.5
        else:
            # For tags, penalize very short terms
            if len(term) < 4:
                prior *= 0.5
            elif len(term) > 8:
                prior *= 1.1  # Slightly boost longer, more specific terms
            
        # If we have document frequency info, calculate IDF component
        if doc_freq is not None and total_docs is not None and total_docs > 0:
            idf = math.log(total_docs / (1 + doc_freq))
            score = tf * idf * prior
        else:
            # Simple frequency-based score
            score = tf * prior * math.log(count + 1)
            
        return score

    def generate_color_groups(self, water_level: int = None, max_groups: int = 60, 
                            file_water_level: int = None, tag_color_scheme: str = 'rainbow',
                            file_color_scheme: str = 'rainbow') -> List[Dict]:
        """Generate color groups for both tags and file patterns
        
        Args:
            water_level: Minimum count for tags (0 = skip tags)
            max_groups: Total color groups (default 60: 30 tags + 30 files)
            file_water_level: Minimum count for file patterns (0 = skip file patterns)
            tag_color_scheme: Color scheme for tags
            file_color_scheme: Color scheme for files
        """
        color_groups = []
        
        # Check if we're including tags (water_level > 0)
        include_tags = water_level is not None and water_level > 0
        # Check if we're including file patterns (file_water_level > 0)
        include_patterns = file_water_level is not None and file_water_level > 0
        
        # Dynamic allocation based on what's included
        if include_tags and include_patterns:
            tag_slots = 30
            file_slots = 30
        elif include_tags:
            tag_slots = 60  # All slots for tags
            file_slots = 0
        elif include_patterns:
            tag_slots = 0
            file_slots = 60  # All slots for file patterns
        else:
            return []  # No color groups
        
        # First, generate tag-based color groups if requested
        if include_tags and tag_slots > 0:
            filtered_tags = self.get_filtered_tags()
            
            if water_level is None:
                water_level = self.calculate_water_level()
            
            # Filter by water level
            above_water_tags = {tag: count for tag, count in filtered_tags.items() 
                               if count >= water_level}
            
            if above_water_tags:
                # Calculate total for normalization
                total_tag_occurrences = sum(above_water_tags.values())
                
                # Calculate Bayesian scores for tags
                tag_scores = {}
                for tag, count in above_water_tags.items():
                    score = self._calculate_bayesian_score(tag, count, total_tag_occurrences)
                    tag_scores[tag] = (score, count)
                
                # Sort by Bayesian score, not just raw count
                sorted_tags = sorted(tag_scores.items(), key=lambda x: x[1][0], reverse=True)
                
                # Limit tags to their allocated slots
                sorted_tags = sorted_tags[:tag_slots]
                
                # Generate colors for tags
                for i, (tag, (score, count)) in enumerate(sorted_tags):
                    rgb = self._get_color_for_index(i, len(sorted_tags), tag_color_scheme, 'tag')
                    rgb_int = self._rgb_to_int(rgb)
                    
                    color_groups.append({
                        "query": f"tag: #{tag}",
                        "color": {
                            "a": 1,
                            "rgb": rgb_int
                        }
                    })
        
        # Now generate file pattern-based color groups if requested
        if include_patterns and self.file_patterns and file_slots > 0:
            # Calculate file pattern water level if not provided
            if file_water_level is None:
                pattern_counts = sorted(self.file_patterns.values())
                if pattern_counts:
                    # Use 90th percentile for file patterns (be more selective)
                    index = int(len(pattern_counts) * 0.1)
                    file_water_level = pattern_counts[-index] if index < len(pattern_counts) else pattern_counts[-1]
                else:
                    file_water_level = 2
            
            # Filter file patterns by water level
            above_water_patterns = {pattern: count for pattern, count in self.file_patterns.items()
                                  if count >= file_water_level}
            
            # Calculate total for normalization
            total_pattern_occurrences = sum(above_water_patterns.values())
            
            # Calculate Bayesian scores for patterns
            pattern_scores = {}
            for pattern, count in above_water_patterns.items():
                # Boost patterns that are likely meaningful (not just fragments)
                score = self._calculate_bayesian_score(pattern, count, total_pattern_occurrences, 
                                                     is_file_pattern=True)
                pattern_scores[pattern] = (score, count)
            
            # Sort by Bayesian score
            sorted_patterns = sorted(pattern_scores.items(), key=lambda x: x[1][0], reverse=True)
            sorted_patterns = sorted_patterns[:file_slots]
            
            # Generate colors for file patterns
            for i, (pattern, (score, count)) in enumerate(sorted_patterns):
                rgb = self._get_color_for_index(i, len(sorted_patterns), file_color_scheme, 'file')
                rgb_int = self._rgb_to_int(rgb)
                
                # Use Obsidian's file query for file patterns
                # file: matches files that contain the pattern in their name
                color_groups.append({
                    "query": f"file: {pattern}",
                    "color": {
                        "a": 1,
                        "rgb": rgb_int
                    }
                })
        
        return color_groups
    
    def _get_color_for_index(self, index: int, total: int, scheme: str, item_type: str) -> Tuple[int, int, int]:
        """Get color for an index based on the selected color scheme"""
        # Normalize position to 0-1
        t = index / (total - 1) if total > 1 else 0
        
        if scheme == 'rainbow':
            # HSL rainbow using golden ratio
            hue = (index * 0.618033988749895) % 1.0
            saturation = 0.7
            lightness = 0.5
            return self._hsl_to_rgb(hue, saturation, lightness)
            
        elif scheme == 'heatmap':
            # Classic heatmap: black -> red -> yellow -> white
            if t < 0.33:
                # Black to red
                r = int(t * 3 * 255)
                g = 0
                b = 0
            elif t < 0.66:
                # Red to yellow
                r = 255
                g = int((t - 0.33) * 3 * 255)
                b = 0
            else:
                # Yellow to white
                r = 255
                g = 255
                b = int((t - 0.66) * 3 * 255)
            return (r, g, b)
            
        elif scheme == 'viridis':
            # Approximate viridis colormap
            r = int(255 * (0.267 + t * (0.004 + t * (0.329 + t * 0.4))))
            g = int(255 * (0.004 + t * (0.704 + t * (0.192 + t * 0.1))))
            b = int(255 * (0.329 + t * (0.456 + t * (-0.785 + t * 1.0))))
            return (min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b)))
            
        elif scheme == 'plasma':
            # Approximate plasma colormap
            r = int(255 * (0.05 + t * (2.35 - t * 1.4)))
            g = int(255 * (0.03 + t * (0.07 + t * 0.9)))
            b = int(255 * (0.53 + t * (0.44 - t * 0.97)))
            return (min(255, max(0, r)), min(255, max(0, g)), min(255, max(0, b)))
            
        elif scheme == 'cool_warm':
            # Cool to warm: blue -> white -> red
            if t < 0.5:
                # Blue to white
                t2 = t * 2
                r = int(t2 * 255)
                g = int(t2 * 255)
                b = 255
            else:
                # White to red
                t2 = (t - 0.5) * 2
                r = 255
                g = int((1 - t2) * 255)
                b = int((1 - t2) * 255)
            return (r, g, b)
            
        elif scheme == 'cool':
            # Cool colors only: deep blue -> cyan -> light green
            if t < 0.5:
                # Deep blue to cyan
                t2 = t * 2
                r = 0
                g = int(t2 * 128)
                b = int(255 - t2 * 127)
            else:
                # Cyan to light green
                t2 = (t - 0.5) * 2
                r = int(t2 * 128)
                g = int(128 + t2 * 127)
                b = int(128 - t2 * 128)
            return (r, g, b)
            
        elif scheme == 'warm':
            # Warm colors only: dark red -> orange -> yellow
            if t < 0.5:
                # Dark red to orange
                t2 = t * 2
                r = int(128 + t2 * 127)
                g = int(t2 * 165)
                b = 0
            else:
                # Orange to yellow
                t2 = (t - 0.5) * 2
                r = 255
                g = int(165 + t2 * 90)
                b = int(t2 * 128)
            return (r, g, b)
            
        elif scheme == 'terrain':
            # Terrain: green valleys -> brown mountains -> white peaks
            if t < 0.4:
                # Green valleys
                t2 = t / 0.4
                r = int(34 + t2 * 102)
                g = int(139 - t2 * 69)
                b = int(34 + t2 * 11)
            elif t < 0.8:
                # Brown mountains
                t2 = (t - 0.4) / 0.4
                r = int(136 + t2 * 65)
                g = int(70 + t2 * 70)
                b = int(45 + t2 * 45)
            else:
                # White peaks
                t2 = (t - 0.8) / 0.2
                r = int(201 + t2 * 54)
                g = int(140 + t2 * 115)
                b = int(90 + t2 * 165)
            return (r, g, b)
            
        elif scheme == 'ocean':
            # Ocean depths: deep blue -> light blue -> aqua
            t2 = t * t  # Quadratic for more deep blues
            r = int(5 + t2 * 75)
            g = int(39 + t * 180)
            b = int(87 + t * 168)
            return (r, g, b)
            
        elif scheme == 'sunset':
            # Sunset: purple -> orange -> yellow
            if t < 0.4:
                # Purple to red
                t2 = t / 0.4
                r = int(75 + t2 * 180)
                g = int(0 + t2 * 69)
                b = int(130 - t2 * 130)
            else:
                # Red to orange to yellow
                t2 = (t - 0.4) / 0.6
                r = 255
                g = int(69 + t2 * 186)
                b = int(0 + t2 * 224)
            return (r, g, b)
            
        elif scheme == 'forest':
            # Forest: dark green -> light green -> yellow
            if t < 0.7:
                # Dark to light green
                t2 = t / 0.7
                r = int(34 + t2 * 100)
                g = int(68 + t2 * 137)
                b = int(34 - t2 * 34)
            else:
                # Light green to yellow
                t2 = (t - 0.7) / 0.3
                r = int(134 + t2 * 121)
                g = int(205 + t2 * 50)
                b = int(0 + t2 * 50)
            return (r, g, b)
            
        elif scheme == 'desert':
            # Desert: brown -> tan -> light yellow
            r = int(139 + t * 116)
            g = int(90 + t * 140)
            b = int(43 + t * 177)
            return (r, g, b)
            
        elif scheme == 'arctic':
            # Arctic: dark blue -> light blue -> white
            if t < 0.6:
                # Dark to light blue
                t2 = t / 0.6
                r = int(25 + t2 * 148)
                g = int(51 + t2 * 165)
                b = int(102 + t2 * 138)
            else:
                # Light blue to white
                t2 = (t - 0.6) / 0.4
                r = int(173 + t2 * 82)
                g = int(216 + t2 * 39)
                b = int(240 + t2 * 15)
            return (r, g, b)
            
        elif scheme == 'lava':
            # Lava flow: black -> red -> orange -> yellow (same as heatmap)
            if t < 0.33:
                # Black to red
                r = int(t * 3 * 255)
                g = 0
                b = 0
            elif t < 0.66:
                # Red to orange
                r = 255
                g = int((t - 0.33) * 3 * 255)
                b = 0
            else:
                # Orange to yellow
                r = 255
                g = 255
                b = int((t - 0.66) * 3 * 128)
            return (r, g, b)
            
        elif scheme == 'turbo':
            # Improved rainbow (Google Turbo colormap approximation)
            if t < 0.2:
                r = int(48 + t * 5 * 30)
                g = int(18 + t * 5 * 60)
                b = int(59 + t * 5 * 196)
            elif t < 0.4:
                t2 = (t - 0.2) * 5
                r = int(78 + t2 * 100)
                g = int(78 + t2 * 177)
                b = int(255 - t2 * 155)
            elif t < 0.6:
                t2 = (t - 0.4) * 5
                r = int(178 + t2 * 77)
                g = 255
                b = int(100 - t2 * 100)
            elif t < 0.8:
                t2 = (t - 0.6) * 5
                r = 255
                g = int(255 - t2 * 140)
                b = 0
            else:
                t2 = (t - 0.8) * 5
                r = int(255 - t2 * 100)
                g = int(115 - t2 * 97)
                b = 0
            return (r, g, b)
            
        elif scheme == 'hsl':
            # Smooth HSL gradient from 0° to 360°
            hue = t  # 0 to 1 maps to 0° to 360°
            saturation = 0.7
            lightness = 0.5
            return self._hsl_to_rgb(hue, saturation, lightness)
            
        elif scheme == 'hsl_inverted':
            # Inverted HSL gradient from 360° to 0°
            hue = 1.0 - t  # 1 to 0 maps to 360° to 0°
            saturation = 0.7
            lightness = 0.5
            return self._hsl_to_rgb(hue, saturation, lightness)
            
        else:
            # Default to rainbow if unknown scheme
            return self._get_color_for_index(index, total, 'rainbow', item_type)
    
    def _hsl_to_rgb(self, h: float, s: float, l: float) -> Tuple[int, int, int]:
        """Convert HSL to RGB"""
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return (int(r * 255), int(g * 255), int(b * 255))
    
    def _rgb_to_int(self, rgb: Tuple[int, int, int]) -> int:
        """Convert RGB tuple to single integer (as Obsidian expects)"""
        r, g, b = rgb
        return (r << 16) | (g << 8) | b
    
    def create_obsidian_config(self, output_path: Path, tag_water_level: int = None, 
                             file_water_level: int = None, tag_color_scheme: str = 'ocean',
                             file_color_scheme: str = 'sunset'):
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
                self._generate_graph_json(target_file, tag_water_level, file_water_level,
                                        tag_color_scheme, file_color_scheme)
            else:
                # Copy other files as-is
                import shutil
                shutil.copy2(template_file, target_file)
        
        return obsidian_dir
    
    def _generate_graph_json(self, graph_file: Path, tag_water_level: int = None,
                           file_water_level: int = None, tag_color_scheme: str = 'ocean',
                           file_color_scheme: str = 'sunset'):
        """Generate graph.json with color groups"""
        # Load template
        template_file = Path(__file__).parent / 'obsidian_templates' / 'graph.json'
        with open(template_file, 'r') as f:
            graph_config = json.load(f)
        
        # Add color groups for both tags and file patterns
        graph_config['colorGroups'] = self.generate_color_groups(
            water_level=tag_water_level,
            file_water_level=file_water_level,
            tag_color_scheme=tag_color_scheme,
            file_color_scheme=file_color_scheme
        )
        
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
    
    def interactive_water_level_adjustment(self) -> Tuple[int, int, str, str]:
        """Allow user to interactively adjust water levels and color schemes for tags and file patterns"""
        stats = self.get_tag_statistics()
        filtered_tags = self.get_filtered_tags()
        
        # Get tag count distribution
        if filtered_tags:
            tag_counts = sorted(filtered_tags.values())
            tag_min = tag_counts[0]
            tag_max = tag_counts[-1]
            tag_median = tag_counts[len(tag_counts) // 2]
        else:
            tag_min = tag_max = tag_median = 0
        
        # Get file pattern count distribution
        if self.file_patterns:
            pattern_counts = sorted(self.file_patterns.values())
            pattern_min = pattern_counts[0]
            pattern_max = pattern_counts[-1]
            pattern_median = pattern_counts[len(pattern_counts) // 2]
        else:
            pattern_min = pattern_max = pattern_median = 0
        
        suggested_tag_level = self.calculate_water_level()
        # For file patterns, also default to 30 for consistency
        suggested_pattern_level = 30 if self.file_patterns else 2
        
        print("\n" + "="*60)
        print("TAG AND FILE PATTERN ANALYSIS COMPLETE")
        print("="*60)
        
        # Tag statistics
        print(f"\nTAG STATISTICS:")
        print(f"Total unique tags found: {stats['total_unique_tags']}")
        print(f"Tags after exclusion filter: {stats['filtered_unique_tags']}")
        print(f"Excluded common tags: {stats['excluded_tags']}")
        print(f"Conversation grouping tags: {stats['conversation_tags']}")
        print(f"Keyword tags: {stats['keyword_tags']}")
        print("\nTag frequency distribution (log scale):")
        print(f"  Maximum count: {tag_max}")
        print(f"  Minimum count: {tag_min}")
        print(f"  Median count: {tag_median}")
        
        # Show log distribution brackets
        if filtered_tags:
            print("\n  Distribution by frequency:")
            for threshold in [100, 50, 30, 20, 10, 5, 2]:
                count_above = len([c for c in filtered_tags.values() if c >= threshold])
                if count_above > 0:
                    print(f"    {threshold}+ occurrences: {count_above} tags")
        
        print(f"\nSuggested tag water level: {suggested_tag_level}")
        tags_above_suggested = len([c for c in filtered_tags.values() if c >= suggested_tag_level])
        print(f"Tags above water level: {tags_above_suggested}")
        
        # File pattern statistics
        print(f"\n\nFILE PATTERN STATISTICS:")
        print(f"Total unique file patterns: {len(self.file_patterns)}")
        if self.file_patterns:
            print("\nFile pattern frequency distribution (log scale):")
            print(f"  Maximum count: {pattern_max}")
            print(f"  Minimum count: {pattern_min}")
            print(f"  Median count: {pattern_median}")
            
            # Show log distribution brackets
            print("\n  Distribution by frequency:")
            for threshold in [100, 50, 30, 20, 10, 5, 2]:
                count_above = len([c for c in self.file_patterns.values() if c >= threshold])
                if count_above > 0:
                    print(f"    {threshold}+ occurrences: {count_above} patterns")
            
            print(f"\nSuggested file pattern water level: {suggested_pattern_level}")
            patterns_above_suggested = len([c for c in self.file_patterns.values() if c >= suggested_pattern_level])
            print(f"File patterns above water level: {patterns_above_suggested}")
        
        # Combined recommendations
        total_groups = tags_above_suggested + (patterns_above_suggested if self.file_patterns else 0)
        if total_groups > 500:
            print(f"\n⚠️  WARNING: {total_groups} total color groups may slow down Obsidian!")
            print("Consider raising water levels to reduce the number of colored items.")
        
        print("\n" + "-"*60)
        print("Water levels determine which items appear colored in the graph.")
        print("Higher water level = fewer items (only most frequent)")
        print("Lower water level = more items (including less frequent)")
        print("\nFor best performance, keep total color groups under 500.")
        print("-"*60)
        
        # Ask if user wants to include tags
        include_tags = True
        tag_level = 0
        tag_color_scheme = 'ocean'
        
        response = input("\nInclude TAG color groups? (Y/n): ").strip().lower()
        if response == 'n':
            include_tags = False
            print("Skipping tag color groups")
        else:
            # Get tag water level (default 30)
            default_tag_level = 30
            while True:
                response = input(f"\nEnter TAG water level (or press Enter for {default_tag_level}): ").strip()
                
                if not response:
                    tag_level = default_tag_level
                    break
                
                try:
                    tag_level = int(response)
                    if tag_level < 1:
                        print("Water level must be at least 1")
                        continue
                        
                    # Show how many tags this would include
                    above_water = len([c for c in filtered_tags.values() if c >= tag_level])
                    print(f"This will include {above_water} tags in the graph")
                    
                    confirm = input("Use this tag water level? (y/N): ").strip().lower()
                    if confirm == 'y':
                        break
                        
                except ValueError:
                    print("Please enter a valid number")
            
            # Get tag color scheme
            print("\nAvailable color schemes (inspired by cartographic ramps):")
            print("  1. rainbow       - Full spectrum rainbow")
            print("  2. terrain       - Green valleys -> Brown mountains -> White peaks")
            print("  3. ocean         - Deep blue -> Light blue -> Aqua")
            print("  4. sunset        - Purple -> Orange -> Yellow")
            print("  5. forest        - Dark green -> Light green -> Yellow")
            print("  6. desert        - Brown -> Tan -> Light yellow")
            print("  7. arctic        - Dark blue -> Light blue -> White")
            print("  8. lava          - Black -> Red -> Orange -> Yellow")
            print("  9. viridis       - Modern perceptual: Purple -> Blue -> Green -> Yellow")
            print(" 10. turbo         - Improved rainbow: Blue -> Green -> Yellow -> Red")
            print(" 11. hsl           - Smooth HSL gradient (0° to 360°)")
            print(" 12. hsl_inverted  - Inverted HSL gradient (360° to 0°)")
            
            scheme_map = {
                '1': 'rainbow', '2': 'terrain', '3': 'ocean', 
                '4': 'sunset', '5': 'forest', '6': 'desert', 
                '7': 'arctic', '8': 'lava', '9': 'viridis', '10': 'turbo',
                '11': 'hsl', '12': 'hsl_inverted'
            }
            
            while True:
                response = input("\nSelect TAG color scheme (1-12, or press Enter for ocean): ").strip()
                if not response:
                    tag_color_scheme = 'ocean'
                    break
                elif response in scheme_map:
                    tag_color_scheme = scheme_map[response]
                    break
                else:
                    print("Please enter a number 1-12")
        
        # Ask if user wants to include file patterns
        include_patterns = True
        pattern_level = 0
        file_color_scheme = 'sunset'
        
        if self.file_patterns:
            response = input("\nInclude FILE PATTERN color groups? (Y/n): ").strip().lower()
            if response == 'n':
                include_patterns = False
                print("Skipping file pattern color groups")
            else:
                # Default to 30 for file patterns too
                default_pattern_level = 30
                while True:
                    response = input(f"\nEnter FILE PATTERN water level (or press Enter for {default_pattern_level}): ").strip()
                    
                    if not response:
                        pattern_level = default_pattern_level
                        break
                    
                    try:
                        pattern_level = int(response)
                        if pattern_level < 1:
                            print("Water level must be at least 1")
                            continue
                            
                        # Show how many patterns this would include
                        above_water = len([c for c in self.file_patterns.values() if c >= pattern_level])
                        print(f"This will include {above_water} file patterns in the graph")
                        
                        confirm = input("Use this file pattern water level? (y/N): ").strip().lower()
                        if confirm == 'y':
                            break
                            
                    except ValueError:
                        print("Please enter a valid number")
                
                # Get file pattern color scheme (reuse scheme_map from above)
                while True:
                    response = input("\nSelect FILE PATTERN color scheme (1-12, or press Enter for sunset): ").strip()
                    if not response:
                        file_color_scheme = 'sunset'
                        break
                    elif response in scheme_map:
                        file_color_scheme = scheme_map[response]
                        break
                    else:
                        print("Please enter a number 1-12")
        else:
            include_patterns = False
            print("\nNo file patterns found to include")
        
        # Return values with inclusion flags
        return tag_level if include_tags else 0, pattern_level if include_patterns else 0, tag_color_scheme, file_color_scheme
    
    def _extract_file_pattern(self, filename: str) -> str:
        """Extract first meaningful word from filename for broader matching"""
        # Remove file extension
        base = filename.rsplit('.', 1)[0] if '.' in filename else filename
        
        # Split by common delimiters
        words = re.split(r'[-_\s]+', base)
        
        # Find the first meaningful word (not a number, not too short)
        for word in words:
            # Skip numbers
            if word.isdigit():
                continue
            
            # Skip common short words
            if word.lower() in {'the', 'a', 'an', 'of', 'to', 'in', 'for', 'and', 'or', 'but'}:
                continue
                
            # Skip too short words
            if len(word) < 3:
                continue
                
            # Return the first meaningful word
            return word
            
        # If no meaningful word found, return None
        return None

    def scan_markdown_files_for_tags(self, output_path: Path):
        """Scan all generated markdown files to collect complete tag counts and file patterns"""
        print("\nScanning all markdown files for tags and file patterns...")
        
        # Reset counts for fresh analysis
        self.tag_counts.clear()
        self.conversation_tags.clear()
        self.keyword_tags.clear()
        self.file_patterns.clear()
        self.file_to_pattern.clear()
        
        md_files = list(output_path.rglob('*.md'))
        print(f"Found {len(md_files)} markdown files to analyze")
        
        # Pattern to find hashtags - more comprehensive
        # Matches #word starting with letter, followed by letters, numbers, hyphens, underscores
        tag_pattern = re.compile(r'#([a-zA-Z][a-zA-Z0-9\-_]*)', re.MULTILINE)
        
        for i, md_file in enumerate(md_files):
            if i % 100 == 0:
                print(f"  Processed {i} files...", end='\r')
                
            try:
                # Extract file pattern
                filename = md_file.name
                pattern = self._extract_file_pattern(filename)
                if pattern:
                    self.file_patterns[pattern] += 1
                    self.file_to_pattern[str(md_file)] = pattern
                
                # Read content for tags
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Find all hashtags
                tags = tag_pattern.findall(content)
                
                for tag in tags:
                    # Determine tag type
                    if tag.startswith('conv-'):
                        self.conversation_tags.add(tag)
                    else:
                        self.keyword_tags.add(tag)
                    
                    self.tag_counts[tag] += 1
                    
            except Exception as e:
                print(f"\nError reading {md_file}: {e}")
        
        print(f"\nScanned {len(md_files)} files")
        print(f"Found {len(self.tag_counts)} unique tags")
        print(f"  Conversation tags: {len(self.conversation_tags)}")
        print(f"  Keyword tags: {len(self.keyword_tags)}")
        print(f"Found {len(self.file_patterns)} unique file patterns")
        
        # Show top file patterns
        if self.file_patterns:
            print("\nTop 10 file patterns:")
            for pattern, count in self.file_patterns.most_common(10):
                print(f"  {pattern}: {count} files")
        
        return len(md_files)
    
    def save_analysis_report(self, output_path: Path, tag_water_level: int, 
                           file_water_level: int = None, tag_color_scheme: str = None,
                           file_color_scheme: str = None):
        """Save a detailed analysis report"""
        stats = self.get_tag_statistics()
        filtered_tags = self.get_filtered_tags()
        
        # Get tags above water level
        above_water_tags = {tag: count for tag, count in filtered_tags.items() 
                           if count >= tag_water_level}
        
        # Get file patterns above water level
        above_water_patterns = {}
        if self.file_patterns and file_water_level:
            above_water_patterns = {pattern: count for pattern, count in self.file_patterns.items()
                                  if count >= file_water_level}
        
        report = {
            'statistics': stats,
            'tag_water_level_used': tag_water_level,
            'file_water_level_used': file_water_level,
            'tag_color_scheme': tag_color_scheme,
            'file_color_scheme': file_color_scheme,
            'tags_in_graph': len(above_water_tags),
            'file_patterns_in_graph': len(above_water_patterns),
            'total_color_groups': len(above_water_tags) + len(above_water_patterns),
            'top_20_tags': dict(sorted(above_water_tags.items(), 
                                     key=lambda x: x[1], 
                                     reverse=True)[:20]),
            'top_20_file_patterns': dict(sorted(above_water_patterns.items(),
                                              key=lambda x: x[1],
                                              reverse=True)[:20]) if above_water_patterns else {},
            'all_filtered_tags': dict(sorted(filtered_tags.items(), 
                                           key=lambda x: x[1], 
                                           reverse=True)),
            'all_file_patterns': dict(sorted(self.file_patterns.items(),
                                           key=lambda x: x[1],
                                           reverse=True))
        }
        
        report_file = output_path / 'tag_analysis_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report_file