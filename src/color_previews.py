#!/usr/bin/env python3
"""
ANSI color preview system for color schemes
Generates 256-color ANSI previews of each color scheme
"""

from typing import List, Tuple, Dict

def rgb_to_ansi256(r: int, g: int, b: int) -> int:
    """Convert RGB to nearest ANSI 256 color code"""
    # Handle grayscale
    if r == g == b:
        if r < 8:
            return 16
        if r > 248:
            return 231
        return round(((r - 8) / 247) * 24) + 232
    
    # Handle colors
    # ANSI 256 uses a 6x6x6 color cube for colors 16-231
    ansi_r = round(r / 255 * 5)
    ansi_g = round(g / 255 * 5)
    ansi_b = round(b / 255 * 5)
    
    return 16 + (36 * ansi_r) + (6 * ansi_g) + ansi_b

def generate_color_block(color_code: int) -> str:
    """Generate an ANSI colored block character"""
    return f"\033[48;5;{color_code}m  \033[0m"

def generate_scheme_preview(scheme_name: str, num_blocks: int = 10) -> str:
    """Generate a preview of a color scheme using ANSI colors"""
    # Import the color generation logic
    from tag_analyzer import TagAnalyzer
    analyzer = TagAnalyzer()
    
    blocks = []
    for i in range(num_blocks):
        t = i / (num_blocks - 1) if num_blocks > 1 else 0
        rgb = analyzer._get_color_for_index(i, num_blocks, scheme_name, 'preview')
        ansi_code = rgb_to_ansi256(*rgb)
        blocks.append(generate_color_block(ansi_code))
    
    return ''.join(blocks)

# Pre-generated color scheme data with ANSI previews
COLOR_SCHEMES = {
    'rainbow': {
        'name': 'rainbow',
        'description': 'Full spectrum rainbow',
        'preview': None  # Will be generated
    },
    'terrain': {
        'name': 'terrain',
        'description': 'Green valleys → Brown mountains → White peaks',
        'preview': None
    },
    'ocean': {
        'name': 'ocean',
        'description': 'Deep blue → Light blue → Aqua',
        'preview': None
    },
    'sunset': {
        'name': 'sunset',
        'description': 'Purple → Orange → Yellow',
        'preview': None
    },
    'forest': {
        'name': 'forest',
        'description': 'Dark green → Light green → Yellow',
        'preview': None
    },
    'desert': {
        'name': 'desert',
        'description': 'Brown → Tan → Light yellow',
        'preview': None
    },
    'arctic': {
        'name': 'arctic',
        'description': 'Dark blue → Light blue → White',
        'preview': None
    },
    'lava': {
        'name': 'lava',
        'description': 'Black → Red → Orange → Yellow',
        'preview': None
    },
    'viridis': {
        'name': 'viridis',
        'description': 'Modern perceptual: Purple → Blue → Green → Yellow',
        'preview': None
    },
    'turbo': {
        'name': 'turbo',
        'description': 'Improved rainbow: Blue → Green → Yellow → Red',
        'preview': None
    },
    'hsl': {
        'name': 'hsl',
        'description': 'Smooth HSL gradient (0° to 360°)',
        'preview': None
    },
    'hsl_inverted': {
        'name': 'hsl_inverted',
        'description': 'Inverted HSL gradient (360° to 0°)',
        'preview': None
    }
}

def initialize_previews():
    """Generate all color previews"""
    for scheme_id, scheme_data in COLOR_SCHEMES.items():
        try:
            scheme_data['preview'] = generate_scheme_preview(scheme_id)
        except Exception as e:
            # Fallback to simple text if preview generation fails
            scheme_data['preview'] = '[preview unavailable]'

def format_color_scheme_menu() -> str:
    """Format the color scheme menu with ANSI previews"""
    initialize_previews()
    
    lines = []
    lines.append("\nAvailable color schemes (with previews):")
    
    # Create numbered list with previews
    scheme_list = list(COLOR_SCHEMES.items())
    for i, (scheme_id, scheme_data) in enumerate(scheme_list, 1):
        # Format: "  1. rainbow       [██████████] - Full spectrum rainbow"
        preview = scheme_data['preview'] or ''
        name = scheme_data['name'].ljust(15)
        desc = scheme_data['description']
        
        line = f"{i:3}. {name} {preview} - {desc}"
        lines.append(line)
    
    return '\n'.join(lines)

def get_scheme_map() -> Dict[str, str]:
    """Get the mapping of menu numbers to scheme IDs"""
    scheme_list = list(COLOR_SCHEMES.keys())
    return {str(i): scheme_id for i, scheme_id in enumerate(scheme_list, 1)}

# Alternative: Simple text representation if ANSI is not supported
def format_color_scheme_menu_simple() -> str:
    """Format the color scheme menu without ANSI colors"""
    lines = []
    lines.append("\nAvailable color schemes:")
    
    scheme_list = list(COLOR_SCHEMES.items())
    for i, (scheme_id, scheme_data) in enumerate(scheme_list, 1):
        name = scheme_data['name'].ljust(15)
        desc = scheme_data['description']
        line = f"{i:3}. {name} - {desc}"
        lines.append(line)
    
    return '\n'.join(lines)

def supports_256_colors() -> bool:
    """Check if terminal supports 256 colors"""
    import os
    term = os.environ.get('TERM', '')
    colorterm = os.environ.get('COLORTERM', '')
    
    # Common terminals that support 256 colors
    if '256color' in term or '256' in term:
        return True
    if colorterm in ['truecolor', '24bit']:
        return True
    if term in ['xterm', 'screen', 'tmux', 'rxvt-unicode', 'konsole', 'gnome-terminal']:
        return True
    
    return False

def test_preview():
    """Test function to show all color scheme previews"""
    print("Color Scheme Previews (256-color ANSI):")
    print("=" * 60)
    
    if supports_256_colors():
        print(format_color_scheme_menu())
    else:
        print("Your terminal doesn't appear to support 256 colors.")
        print("Showing simple menu instead:")
        print(format_color_scheme_menu_simple())

if __name__ == "__main__":
    test_preview()