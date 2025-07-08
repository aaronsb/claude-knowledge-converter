#!/usr/bin/env python3
"""
High-performance tag analysis tool to scan all documents and rank tags by frequency
"""

import re
import json
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple
import multiprocessing as mp
from functools import partial

def extract_tags_from_file(file_path: Path) -> List[str]:
    """Extract all hashtags from a single file"""
    tags = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find all hashtags - more comprehensive pattern
        # Matches #word, #word-with-dashes, #word_with_underscores
        tag_pattern = re.compile(r'#([a-zA-Z][a-zA-Z0-9\-_]*)', re.MULTILINE)
        tags = tag_pattern.findall(content)
        
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return tags

def process_files_chunk(files_chunk: List[Path]) -> Counter:
    """Process a chunk of files and return tag counts"""
    local_counter = Counter()
    
    for file_path in files_chunk:
        tags = extract_tags_from_file(file_path)
        local_counter.update(tags)
    
    return local_counter

def analyze_all_tags(base_path: Path, num_processes: int = None) -> Dict[str, int]:
    """Analyze all markdown files in parallel for maximum performance"""
    # Collect all markdown files
    print("Collecting markdown files...")
    md_files = list(base_path.rglob('*.md'))
    print(f"Found {len(md_files)} markdown files to analyze")
    
    if not md_files:
        return {}
    
    # Determine number of processes
    if num_processes is None:
        num_processes = min(mp.cpu_count(), 8)  # Cap at 8 for memory efficiency
    
    # Split files into chunks for parallel processing
    chunk_size = max(1, len(md_files) // num_processes)
    file_chunks = [md_files[i:i + chunk_size] for i in range(0, len(md_files), chunk_size)]
    
    print(f"Processing files using {num_processes} processes...")
    
    # Process files in parallel
    with mp.Pool(processes=num_processes) as pool:
        chunk_counters = pool.map(process_files_chunk, file_chunks)
    
    # Combine all counters
    print("Combining results...")
    total_counter = Counter()
    for counter in chunk_counters:
        total_counter.update(counter)
    
    return dict(total_counter)

def analyze_tag_distribution(tag_counts: Dict[str, int]) -> None:
    """Analyze and display tag distribution statistics"""
    if not tag_counts:
        print("No tags found!")
        return
    
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\nTotal unique tags: {len(tag_counts)}")
    print(f"Total tag occurrences: {sum(tag_counts.values())}")
    
    # Show top 50 tags
    print("\nTop 50 tags by frequency:")
    print("-" * 60)
    print(f"{'Rank':<6} {'Tag':<30} {'Count':<10} {'%':<6}")
    print("-" * 60)
    
    total_occurrences = sum(tag_counts.values())
    
    for i, (tag, count) in enumerate(sorted_tags[:50], 1):
        percentage = (count / total_occurrences) * 100
        print(f"{i:<6} #{tag:<29} {count:<10} {percentage:>5.1f}%")
    
    # Show distribution statistics
    counts = list(tag_counts.values())
    counts.sort(reverse=True)
    
    print("\n" + "-" * 60)
    print("Tag frequency distribution:")
    print(f"  Max count: {counts[0]}")
    print(f"  Min count: {counts[-1]}")
    print(f"  Median count: {counts[len(counts)//2]}")
    print(f"  Tags with 1 occurrence: {counts.count(1)}")
    print(f"  Tags with 2+ occurrences: {len([c for c in counts if c >= 2])}")
    print(f"  Tags with 5+ occurrences: {len([c for c in counts if c >= 5])}")
    print(f"  Tags with 10+ occurrences: {len([c for c in counts if c >= 10])}")
    print(f"  Tags with 30+ occurrences: {len([c for c in counts if c >= 30])}")
    print(f"  Tags with 50+ occurrences: {len([c for c in counts if c >= 50])}")
    print(f"  Tags with 100+ occurrences: {len([c for c in counts if c >= 100])}")

def save_full_report(tag_counts: Dict[str, int], output_path: Path) -> None:
    """Save a comprehensive tag report"""
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    
    report = {
        'total_unique_tags': len(tag_counts),
        'total_occurrences': sum(tag_counts.values()),
        'all_tags_ranked': [{'tag': tag, 'count': count} for tag, count in sorted_tags],
        'tags_by_frequency_tier': {
            '100+': [tag for tag, count in sorted_tags if count >= 100],
            '50-99': [tag for tag, count in sorted_tags if 50 <= count < 100],
            '30-49': [tag for tag, count in sorted_tags if 30 <= count < 50],
            '10-29': [tag for tag, count in sorted_tags if 10 <= count < 30],
            '5-9': [tag for tag, count in sorted_tags if 5 <= count < 10],
            '2-4': [tag for tag, count in sorted_tags if 2 <= count < 5],
            '1': [tag for tag, count in sorted_tags if count == 1]
        }
    }
    
    report_file = output_path / 'comprehensive_tag_analysis.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nFull report saved to: {report_file}")

def main():
    """Run comprehensive tag analysis"""
    import sys
    
    if len(sys.argv) > 1:
        base_path = Path(sys.argv[1])
    else:
        base_path = Path('output/claude_history')
    
    if not base_path.exists():
        print(f"Error: Path {base_path} does not exist!")
        return
    
    print(f"Analyzing tags in: {base_path}")
    print("=" * 60)
    
    # Perform analysis
    tag_counts = analyze_all_tags(base_path)
    
    # Display results
    analyze_tag_distribution(tag_counts)
    
    # Save comprehensive report
    save_full_report(tag_counts, base_path)
    
    # Check if #semantic is in the results
    if 'semantic' in tag_counts:
        print(f"\n✓ Found #semantic tag: {tag_counts['semantic']} occurrences")
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        rank = next(i for i, (tag, _) in enumerate(sorted_tags, 1) if tag == 'semantic')
        print(f"  Rank: #{rank} out of {len(tag_counts)} tags")
    else:
        print("\n✗ #semantic tag not found in any documents")

if __name__ == "__main__":
    main()