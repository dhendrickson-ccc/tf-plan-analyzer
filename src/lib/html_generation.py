"""
HTML Generation Utilities

This module consolidates all CSS and HTML generation logic that was previously
duplicated across analyze_plan.py and multi_env_comparator.py.

Functions:
    get_base_css() -> str: Returns base CSS for typography, layout, and containers
    get_diff_highlight_css() -> str: Returns CSS for diff highlighting (removed/added/unchanged)
    get_summary_card_css() -> str: Returns CSS for summary cards (total/created/updated/deleted)
    get_resource_card_css() -> str: Returns CSS for resource cards and expandable sections
    generate_full_styles() -> str: Returns complete <style> block combining all CSS
"""


def get_base_css() -> str:
    """
    Get base CSS for typography, layout, and containers.

    Returns:
        str: CSS stylesheet with foundational styles including:
            - CSS reset (margin, padding, box-sizing)
            - Body typography (font family, colors, line height)
            - Container styles (max-width, shadows, border-radius)
            - Header styling (gradient background)
            - Responsive design rules

    Example:
        >>> css = get_base_css()
        >>> "font-family" in css
        True
    """
    return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        header p {
            font-size: 1em;
            opacity: 0.9;
        }
        
        .section {
            padding: 30px;
        }
        
        .section-header {
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            color: #667eea;
        }
        
        @media (max-width: 768px) {
            .change-diff {
                grid-template-columns: 1fr;
            }
            
            .summary {
                grid-template-columns: 1fr;
            }
        }
"""


def get_summary_card_css() -> str:
    """
    Get CSS for summary cards displaying metrics.

    Returns:
        str: CSS stylesheet for summary cards including:
            - Grid layout for responsive card placement
            - Card styling (background, padding, shadows)
            - Number and label typography
            - Semantic color coding (total=purple, created=green, updated=orange, deleted=red)

    Example:
        >>> css = get_summary_card_css()
        >>> ".summary-card" in css
        True
    """
    return """
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }
        
        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            text-align: center;
        }
        
        .summary-card .number {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        
        .summary-card .label {
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        
        .summary-card.total .number { color: #667eea; }
        .summary-card.created .number { color: #51cf66; }
        .summary-card.updated .number { color: #ffa94d; }
        .summary-card.deleted .number { color: #ff6b6b; }
"""


def get_diff_highlight_css() -> str:
    """
    Get CSS for diff highlighting (removed/added/unchanged values).

    Returns:
        str: CSS stylesheet for diff visualization including:
            - Line-level highlighting (.removed, .added, .unchanged)
            - Character-level highlighting (.char-removed, .char-added)
            - Known-after-apply highlighting (.known-after-apply)
            - Baseline comparison styles (.baseline-removed, .baseline-added)
            - Opacity utilities for faded text

    Example:
        >>> css = get_diff_highlight_css()
        >>> ".char-removed" in css
        True
    """
    return """
        .unchanged {
            color: #666;
        }
        
        .opacity-50 {
            opacity: 0.3;
        }
        
        .removed {
            background-color: #ffe0e0;
            color: #c92a2a;
            display: block;
        }
        
        .added {
            background-color: #d3f9d8;
            color: #2b8a3e;
            display: block;
        }
        
        .known-after-apply {
            background-color: #fff4e6;
            color: #e67700;
            display: block;
        }
        
        .char-removed {
            background-color: #ff9999;
            color: #7d0000;
        }
        
        .char-added {
            background-color: #99ff99;
            color: #006600;
        }
        
        .char-known-after-apply {
            background-color: #ffe8a1;
            color: #995700;
        }
        
        .baseline-removed {
            background-color: #bbdefb;
            color: #0d47a1;
            display: block;
        }
        
        .baseline-added {
            background-color: #c8e6c9;
            color: #1b5e20;
            display: block;
        }
        
        .baseline-char-removed {
            background-color: #90caf9;
            color: #01579b;
        }
        
        .baseline-char-added {
            background-color: #81c784;
            color: #2e7d32;
        }
"""


def get_resource_card_css() -> str:
    """
    Get CSS for resource cards and expandable sections.

    Returns:
        str: CSS stylesheet for resource display including:
            - Resource list grids
            - Resource item styling with left border color coding
            - Expandable resource change cards with toggle functionality
            - Diff column layouts (before/after comparison)
            - JSON content display (monospace, pre-wrap)
            - Change item styling and attribute displays
            - Sensitive badge styling
            - Legend/help section styling
            - Ignored resources/fields styling
            - Toggle buttons and interactive elements

    Example:
        >>> css = get_resource_card_css()
        >>> ".resource-card" in css
        True
    """
    return """
        .resource-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .resource-list.hidden {
            display: none;
        }
        
        .resource-item {
            background: #f8f9fa;
            padding: 12px 15px;
            border-radius: 5px;
            font-family: Monaco, Menlo, Consolas, 'Courier New', monospace;
            font-size: 0.9em;
            border-left: 4px solid #51cf66;
            word-wrap: break-word;
            overflow-wrap: break-word;
            word-break: break-all;
        }
        
        .resource-change {
            background: #fff;
            margin-bottom: 20px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            overflow: hidden;
        }
        
        .resource-change-header {
            background: #f8f9fa;
            padding: 15px 20px;
            font-family: Monaco, Menlo, Consolas, 'Courier New', monospace;
            font-weight: bold;
            font-size: 1.1em;
            color: #495057;
            border-bottom: 2px solid #ffa94d;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .resource-change-header:hover {
            background: #e9ecef;
        }
        
        .toggle-icon {
            cursor: pointer;
            user-select: none;
            flex-shrink: 0;
            width: 20px;
            transition: transform 0.3s;
            font-size: 0.9em;
        }
        
        .toggle-icon.collapsed {
            transform: rotate(-90deg);
        }
        
        .resource-name {
            user-select: text;
            cursor: text;
            flex: 1;
        }
        
        .resource-change-content {
            padding: 20px;
        }
        
        .resource-change-content.hidden {
            display: none;
        }
        
        .change-item {
            margin-bottom: 25px;
            border-left: 3px solid #ffa94d;
            padding-left: 15px;
        }
        
        .change-attribute {
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
            font-size: 1.05em;
        }
        
        .sensitive-badge {
            background: #ff6b6b;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: bold;
            margin-left: 8px;
            vertical-align: middle;
        }
        
        .change-diff {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 10px;
        }
        
        .diff-column {
            background: #f8f9fa;
            border-radius: 5px;
            overflow: hidden;
        }
        
        .diff-header {
            padding: 8px 12px;
            font-weight: bold;
            font-size: 0.85em;
            text-transform: uppercase;
        }
        
        .diff-header.before {
            background: #ffe0e0;
            color: #c92a2a;
        }
        
        .diff-header.after {
            background: #d3f9d8;
            color: #2b8a3e;
        }
        
        .diff-header.after-unknown {
            background: #fff4e6;
            color: #e67700;
        }
        
        .json-content {
            padding: 12px;
            margin: 0;
            overflow-x: auto;
            font-family: Monaco, Menlo, Consolas, 'Courier New', monospace;
            font-size: 0.85em;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .simple-change {
            font-family: Monaco, Menlo, Consolas, 'Courier New', monospace;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        
        .simple-change .before {
            color: #c92a2a;
            text-decoration: line-through;
        }
        
        .simple-change .after {
            color: #2b8a3e;
            font-weight: bold;
        }
        
        .simple-change .after.known-after-apply {
            color: #e67700;
            background-color: #fff4e6;
            padding: 2px 6px;
            border-radius: 3px;
        }
        
        .toggle-all {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            margin-bottom: 20px;
        }
        
        .toggle-all:hover {
            background: #5568d3;
        }
        
        .resource-type-section {
            margin-bottom: 30px;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
        }
        
        .resource-type-section h3 {
            color: #667eea;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .ignored-field {
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 5px;
            border-left: 4px solid #868e96;
        }
        
        .ignored-field-header {
            margin-bottom: 10px;
            color: #495057;
        }
        
        .ignored-resources-list {
            list-style-type: none;
            padding-left: 0;
            margin: 0;
        }
        
        .ignored-resources-list li {
            padding: 5px 10px;
            margin: 3px 0;
            background: #f1f3f5;
            border-radius: 3px;
            font-family: Monaco, Menlo, Consolas, 'Courier New', monospace;
            font-size: 0.9em;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        
        .ignored-resources-list .more-indicator {
            background: #e9ecef;
            color: #868e96;
            font-style: italic;
            font-family: inherit;
        }
        
        .legend {
            background: #f8f9fa;
            border: 2px solid #667eea;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 30px;
        }
        
        .legend h2 {
            margin-top: 0;
            color: #667eea;
            font-size: 1.3em;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .legend-content {
            margin-top: 15px;
        }
        
        .legend-content.hidden {
            display: none;
        }
        
        .legend-section {
            margin-bottom: 20px;
        }
        
        .legend-section h3 {
            color: #495057;
            font-size: 1.1em;
            margin-bottom: 10px;
        }
        
        .legend-item {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            margin-bottom: 8px;
            padding: 8px;
            background: white;
            border-radius: 4px;
        }
        
        .legend-symbol {
            font-weight: bold;
            min-width: 30px;
        }
        
        .legend-description {
            flex: 1;
        }
"""


def get_attribute_section_css() -> str:
    """
    Get CSS for attribute header-based layout (v2.0).

    Replaces table-based attribute layout with flexbox sections.
    Each attribute becomes a header with horizontally aligned environment values.

    Returns:
        str: CSS stylesheet for attribute sections including:
            - .attribute-section: Container with spacing and shadow
            - .attribute-header: H3-styled attribute name
            - .attribute-values: Flexbox container for environment columns
            - .env-value-column: Individual environment value wrapper
            - .env-label: Environment name label

    Example:
        >>> css = get_attribute_section_css()
        >>> ".attribute-section" in css
        True
    """
    return """
        .attribute-section {
            margin-bottom: 30px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .attribute-header {
            font-size: 1.2em;
            margin: 0 0 15px 0;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
            color: #495057;
        }
        
        .attribute-header code {
            font-family: Monaco, Menlo, Consolas, 'Courier New', monospace;
            color: #667eea;
        }
        
        .attribute-values {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        
        .env-value-column {
            flex: 1;
            min-width: 250px;
        }
        
        .env-label {
            font-weight: 600;
            color: #495057;
            margin-bottom: 8px;
            padding: 8px 12px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 0.95em;
        }
        
        .sensitive-badge {
            background: #dc3545;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.75em;
            margin-left: 10px;
            display: inline-block;
        }
"""


def generate_full_styles() -> str:
    """
    Generate complete <style> block combining all CSS functions.

    This is the main entry point for getting all CSS. It combines:
    - Base typography and layout (get_base_css)
    - Summary cards with semantic colors (get_summary_card_css)
    - Diff highlighting for before/after comparison (get_diff_highlight_css)
    - Resource cards with expandable sections (get_resource_card_css)
    - Attribute sections with header-based layout (get_attribute_section_css)

    Returns:
        str: Complete HTML <style> block ready for insertion in <head>

    Example:
        >>> styles = generate_full_styles()
        >>> styles.startswith("<style>")
        True
        >>> styles.endswith("</style>")
        True
        >>> "font-family" in styles
        True

    Usage in HTML generation:
        >>> html = f'''
        ... <html>
        ... <head>
        ...     {generate_full_styles()}
        ... </head>
        ... <body>...</body>
        ... </html>
        ... '''
    """
    return f"""<style>
{get_base_css()}
{get_summary_card_css()}
{get_diff_highlight_css()}
{get_resource_card_css()}
{get_attribute_section_css()}
</style>"""
