#!/usr/bin/env python3
"""
DEPRECATED: This script is deprecated in favor of the built-in HTML generation
in analyze_plan.py. 

Instead of:
    python analyze_plan.py plan.json -v > report.txt
    python generate_html_report.py report.txt report.html

Use:
    python analyze_plan.py plan.json --config ignore_config.json --html report.html

This new approach:
- Generates HTML directly from the Terraform plan JSON
- Eliminates the intermediate text parsing step
- Provides more accurate diff highlighting
- Maintains all the same visual features

This script is kept for backward compatibility but may be removed in the future.

---

Generate an HTML report from the Terraform plan analysis text report.
This script creates a visually appealing HTML report with diff highlighting
to show exactly what changes for each resource.
"""

import json
import re
import sys
from difflib import SequenceMatcher, unified_diff
from typing import Dict, List, Any, Tuple
import html


def highlight_json_diff(before: Any, after: Any) -> Tuple[str, str]:
    """
    Highlight differences between two JSON structures.
    Returns HTML for before and after with differences highlighted.
    Only highlights lines that are actually different.
    """
    # Convert to formatted JSON strings
    before_str = json.dumps(before, indent=2, sort_keys=True) if before is not None else ""
    after_str = json.dumps(after, indent=2, sort_keys=True) if after is not None else ""
    
    # If strings are identical, return without highlighting
    if before_str == after_str:
        before_html = f'<pre class="json-content">{html.escape(before_str)}</pre>'
        after_html = f'<pre class="json-content">{html.escape(after_str)}</pre>'
        return before_html, after_html
    
    # Split into lines for comparison
    before_lines = before_str.split('\n')
    after_lines = after_str.split('\n')
    
    # Use SequenceMatcher to find differences
    matcher = SequenceMatcher(None, before_lines, after_lines)
    
    before_html_lines = []
    after_html_lines = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # Lines are the same
            for line in before_lines[i1:i2]:
                before_html_lines.append(f'<span class="unchanged">{html.escape(line)}</span>')
            for line in after_lines[j1:j2]:
                after_html_lines.append(f'<span class="unchanged">{html.escape(line)}</span>')
        elif tag == 'delete':
            # Lines only in before
            for line in before_lines[i1:i2]:
                before_html_lines.append(f'<span class="removed">{html.escape(line)}</span>')
            # Add empty lines to after to maintain alignment
            empty_line = '<span class="unchanged opacity-50">' + ('&nbsp;' * 20) + '</span>'
            for _ in range(i2 - i1):
                after_html_lines.append(empty_line)
        elif tag == 'insert':
            # Lines only in after
            # Add empty lines to before to maintain alignment
            empty_line = '<span class="unchanged opacity-50">' + ('&nbsp;' * 20) + '</span>'
            for _ in range(j2 - j1):
                before_html_lines.append(empty_line)
            for line in after_lines[j1:j2]:
                after_html_lines.append(f'<span class="added">{html.escape(line)}</span>')
        elif tag == 'replace':
            # Lines differ - do character-level comparison for similar lines
            before_chunk = before_lines[i1:i2]
            after_chunk = after_lines[j1:j2]
            
            # For each pair of lines, check if they're similar (e.g., only value differs)
            max_len = max(len(before_chunk), len(after_chunk))
            empty_line = '<span class="unchanged opacity-50">' + ('&nbsp;' * 20) + '</span>'
            for idx in range(max_len):
                if idx < len(before_chunk):
                    before_line = before_chunk[idx]
                    # Check if this line exists in after_chunk
                    if before_line in after_chunk:
                        before_html_lines.append(f'<span class="unchanged">{html.escape(before_line)}</span>')
                    else:
                        before_html_lines.append(f'<span class="removed">{html.escape(before_line)}</span>')
                else:
                    before_html_lines.append(empty_line)
                
                if idx < len(after_chunk):
                    after_line = after_chunk[idx]
                    # Check if this line exists in before_chunk
                    if after_line in before_chunk:
                        after_html_lines.append(f'<span class="unchanged">{html.escape(after_line)}</span>')
                    else:
                        after_html_lines.append(f'<span class="added">{html.escape(after_line)}</span>')
                else:
                    after_html_lines.append(empty_line)
    
    before_html = f'<pre class="json-content">{"<br>".join(before_html_lines)}</pre>'
    after_html = f'<pre class="json-content">{"<br>".join(after_html_lines)}</pre>'
    
    return before_html, after_html


def parse_text_report(report_path: str) -> Dict[str, Any]:
    """Parse the text report and extract structured data."""
    with open(report_path, 'r') as f:
        content = f.read()
    
    # Parse summary
    summary = {}
    summary_match = re.search(
        r'Total Resources:\s+(\d+)\s+Created:\s+(\d+)\s+Imported:\s+(\d+)\s+Updated:\s+(\d+)\s+- Tag-only:\s+(\d+)\s+- Config changes:\s+(\d+)\s+Deleted:\s+(\d+)',
        content
    )
    if summary_match:
        summary = {
            'total': int(summary_match.group(1)),
            'created': int(summary_match.group(2)),
            'imported': int(summary_match.group(3)),
            'updated': int(summary_match.group(4)),
            'tag_only': int(summary_match.group(5)),
            'config_changes': int(summary_match.group(6)),
            'deleted': int(summary_match.group(7))
        }
    
    # Parse created resources
    created = []
    created_section = re.search(r'CREATED \((\d+)\)\s*-+\s*(.*?)\n\nUPDATED', content, re.DOTALL)
    if created_section:
        lines = created_section.group(2).strip().split('\n')
        created = [line.strip() for line in lines if line.strip()]
    
    # Parse updated resources with changes
    updated = []
    updated_section = re.search(r'UPDATED - CONFIG CHANGES.*?\n-+\n(.*?)(?:\n\n[A-Z]|$)', content, re.DOTALL)
    if updated_section:
        # Split by resource blocks
        resource_blocks = re.split(r'\n  ([a-z_]+\.[a-z_0-9\[\]"]+)\n', updated_section.group(1))
        
        current_resource = None
        current_changes = []
        
        for i, block in enumerate(resource_blocks):
            if i % 2 == 1:  # Resource name
                if current_resource:
                    updated.append({
                        'name': current_resource,
                        'changes': parse_changes('\n'.join(current_changes))
                    })
                current_resource = block
                current_changes = []
            elif current_resource:  # Change content
                current_changes.append(block)
        
        # Add the last resource
        if current_resource:
            updated.append({
                'name': current_resource,
                'changes': parse_changes('\n'.join(current_changes))
            })
    
    return {
        'summary': summary,
        'created': created,
        'updated': updated
    }


def parse_changes(change_text: str) -> List[Dict[str, Any]]:
    """Parse individual changes for a resource."""
    changes = []
    
    # Split by attribute (lines starting with •)
    attributes = re.split(r'\n\s+•\s+', change_text)
    
    for attr in attributes:
        if not attr.strip():
            continue
        
        # Extract attribute name
        attr_match = re.match(r'([^:]+):\s*(.*)', attr, re.DOTALL)
        if not attr_match:
            continue
        
        attr_name = attr_match.group(1).strip()
        attr_content = attr_match.group(2).strip()
        
        # Extract before (lines with -) and after (lines with +)
        # For complex structures, we need to extract the complete JSON blocks
        before_lines = []
        after_lines = []
        
        lines = attr_content.split('\n')
        in_before = False
        in_after = False
        seen_blank_after_content = False
        
        for line in lines:
            stripped = line.lstrip()
            
            # If we see a blank line after collecting content, mark it
            if not stripped and (before_lines or after_lines):
                seen_blank_after_content = True
                # Add the blank line if we're in a block
                if in_before:
                    before_lines.append('')
                elif in_after:
                    after_lines.append('')
                continue
            
            # If we've seen a blank line and now see non-diff content, stop
            if seen_blank_after_content and stripped and not stripped.startswith('-') and not stripped.startswith('+'):
                break
            
            # Reset blank line flag when we see diff markers
            if stripped.startswith('-') or stripped.startswith('+'):
                seen_blank_after_content = False
            
            if stripped.startswith('- '):
                in_before = True
                in_after = False
                before_lines.append(stripped[2:])  # Remove '- ' prefix
            elif stripped.startswith('+ '):
                in_before = False
                in_after = True
                after_lines.append(stripped[2:])  # Remove '+ ' prefix
            elif stripped.startswith('-') and len(stripped) > 1 and stripped[1] in ' \t':
                # Line starts with '- ' (dash followed by space/tab)
                in_before = True
                in_after = False
                before_lines.append(stripped[1:].lstrip())  # Remove '-' and leading whitespace
            elif stripped.startswith('+') and len(stripped) > 1 and stripped[1] in ' \t':
                # Line starts with '+ ' (plus followed by space/tab)
                in_before = False
                in_after = True
                after_lines.append(stripped[1:].lstrip())  # Remove '+' and leading whitespace
            elif in_before and not stripped.startswith('+'):
                # Continuation of before block (includes lines that don't start with +)
                if stripped:
                    before_lines.append(stripped)
            elif in_after and not stripped.startswith('-'):
                # Continuation of after block (includes lines that don't start with -)
                if stripped:
                    after_lines.append(stripped)
        
        # Try to parse the collected lines as JSON
        before = None
        after = None
        
        if before_lines:
            before_str = '\n'.join(before_lines)
            try:
                before = json.loads(before_str)
            except:
                # If it's a quoted string with escape sequences, try to decode it
                try:
                    before = json.loads(f'"{before_str}"') if not before_str.startswith('"') else json.loads(before_str)
                except:
                    before = before_str
        
        if after_lines:
            after_str = '\n'.join(after_lines)
            try:
                after = json.loads(after_str)
            except:
                # If it's a quoted string with escape sequences, try to decode it
                try:
                    after = json.loads(f'"{after_str}"') if not after_str.startswith('"') else json.loads(after_str)
                except:
                    after = after_str
        
        if before is not None or after is not None:
            changes.append({
                'attribute': attr_name,
                'before': before,
                'after': after,
                'raw': attr_content
            })
        else:
            # Complex change, store raw content
            changes.append({
                'attribute': attr_name,
                'raw': attr_content,
                'complex': True
            })
    
    return changes


def generate_html_report(data: Dict[str, Any], output_path: str):
    """Generate the HTML report."""
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terraform Plan Analysis Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 2px solid #e9ecef;
        }}
        
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            text-align: center;
        }}
        
        .summary-card .number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .summary-card .label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
        }}
        
        .summary-card.total .number {{ color: #667eea; }}
        .summary-card.created .number {{ color: #51cf66; }}
        .summary-card.updated .number {{ color: #ffa94d; }}
        .summary-card.deleted .number {{ color: #ff6b6b; }}
        
        .section {{
            padding: 30px;
        }}
        
        .section-header {{
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
            color: #667eea;
        }}
        
        .resource-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }}
        
        .resource-item {{
            background: #f8f9fa;
            padding: 12px 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            border-left: 4px solid #51cf66;
        }}
        
        .resource-change {{
            background: #fff;
            margin-bottom: 20px;
            border-radius: 8px;
            border: 1px solid #e9ecef;
            overflow: hidden;
        }}
        
        .resource-change-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            font-size: 1.1em;
            color: #495057;
            border-bottom: 2px solid #ffa94d;
            cursor: pointer;
            user-select: none;
        }}
        
        .resource-change-header:hover {{
            background: #e9ecef;
        }}
        
        .resource-change-header::before {{
            content: '▼ ';
            display: inline-block;
            transition: transform 0.3s;
        }}
        
        .resource-change-header.collapsed::before {{
            transform: rotate(-90deg);
        }}
        
        .resource-change-content {{
            padding: 20px;
        }}
        
        .resource-change-content.hidden {{
            display: none;
        }}
        
        .change-item {{
            margin-bottom: 25px;
            border-left: 3px solid #ffa94d;
            padding-left: 15px;
        }}
        
        .change-attribute {{
            font-weight: bold;
            color: #495057;
            margin-bottom: 10px;
            font-size: 1.05em;
        }}
        
        .change-diff {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 10px;
        }}
        
        .diff-column {{
            background: #f8f9fa;
            border-radius: 5px;
            overflow: hidden;
        }}
        
        .diff-header {{
            padding: 8px 12px;
            font-weight: bold;
            font-size: 0.85em;
            text-transform: uppercase;
        }}
        
        .diff-header.before {{
            background: #ffe0e0;
            color: #c92a2a;
        }}
        
        .diff-header.after {{
            background: #d3f9d8;
            color: #2b8a3e;
        }}
        
        .json-content {{
            padding: 12px;
            margin: 0;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
            line-height: 1.5;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .unchanged {{
            color: #666;
        }}
        
        .opacity-50 {{
            opacity: 0.3;
        }}
        
        .removed {{
            background-color: #ffe0e0;
            color: #c92a2a;
            display: block;
        }}
        
        .added {{
            background-color: #d3f9d8;
            color: #2b8a3e;
            display: block;
        }}
        
        .simple-change {{
            font-family: 'Courier New', monospace;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        
        .simple-change .before {{
            color: #c92a2a;
            text-decoration: line-through;
        }}
        
        .simple-change .after {{
            color: #2b8a3e;
            font-weight: bold;
        }}
        
        .toggle-all {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            margin-bottom: 20px;
        }}
        
        .toggle-all:hover {{
            background: #5568d3;
        }}
        
        @media (max-width: 768px) {{
            .change-diff {{
                grid-template-columns: 1fr;
            }}
            
            .summary {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Terraform Plan Analysis Report</h1>
            <p>Generated on {re.sub(r'[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}}', '2026-01-12', 'January 12, 2026')}</p>
        </header>
        
        <div class="summary">
            <div class="summary-card total">
                <div class="number">{data['summary'].get('total', 0)}</div>
                <div class="label">Total Resources</div>
            </div>
            <div class="summary-card created">
                <div class="number">{data['summary'].get('created', 0)}</div>
                <div class="label">Created</div>
            </div>
            <div class="summary-card updated">
                <div class="number">{data['summary'].get('config_changes', 0)}</div>
                <div class="label">Updated</div>
            </div>
            <div class="summary-card deleted">
                <div class="number">{data['summary'].get('deleted', 0)}</div>
                <div class="label">Deleted</div>
            </div>
        </div>
"""
    
    # Created resources section
    if data['created']:
        html_content += """
        <div class="section">
            <h2 class="section-header">📦 Created Resources</h2>
            <div class="resource-list">
"""
        for resource in data['created']:
            html_content += f'                <div class="resource-item">{html.escape(resource)}</div>\n'
        
        html_content += """            </div>
        </div>
"""
    
    # Updated resources section
    if data['updated']:
        html_content += """
        <div class="section">
            <h2 class="section-header">🔄 Updated Resources</h2>
            <button class="toggle-all" onclick="toggleAll()">Expand/Collapse All</button>
"""
        
        for resource in data['updated']:
            resource_name = html.escape(resource['name'])
            html_content += f"""
            <div class="resource-change">
                <div class="resource-change-header" onclick="toggleResource(this)">
                    {resource_name}
                </div>
                <div class="resource-change-content">
"""
            
            for change in resource['changes']:
                attr_name = html.escape(change['attribute'])
                html_content += f"""
                    <div class="change-item">
                        <div class="change-attribute">{attr_name}</div>
"""
                
                if 'complex' in change and change['complex']:
                    # Complex change - just show raw content
                    raw_content = html.escape(change.get('raw', ''))
                    html_content += f"""
                        <pre class="json-content">{raw_content}</pre>
"""
                else:
                    before = change.get('before')
                    after = change.get('after')
                    
                    # Check if it's a simple value or complex structure
                    if isinstance(before, (dict, list)) or isinstance(after, (dict, list)):
                        # Complex structure - use diff highlighting
                        before_html, after_html = highlight_json_diff(before, after)
                        html_content += f"""
                        <div class="change-diff">
                            <div class="diff-column">
                                <div class="diff-header before">Before</div>
                                {before_html}
                            </div>
                            <div class="diff-column">
                                <div class="diff-header after">After</div>
                                {after_html}
                            </div>
                        </div>
"""
                    else:
                        # Simple value change
                        before_str = html.escape(str(before) if before is not None else 'null')
                        after_str = html.escape(str(after) if after is not None else 'null')
                        html_content += f"""
                        <div class="simple-change">
                            <span class="before">{before_str}</span> → <span class="after">{after_str}</span>
                        </div>
"""
                
                html_content += """
                    </div>
"""
            
            html_content += """
                </div>
            </div>
"""
        
        html_content += """
        </div>
"""
    
    # JavaScript for toggling
    html_content += """
    </div>
    
    <script>
        function toggleResource(header) {
            header.classList.toggle('collapsed');
            const content = header.nextElementSibling;
            content.classList.toggle('hidden');
        }
        
        function toggleAll() {
            const headers = document.querySelectorAll('.resource-change-header');
            const firstHeader = headers[0];
            const shouldExpand = firstHeader.classList.contains('collapsed');
            
            headers.forEach(header => {
                const content = header.nextElementSibling;
                if (shouldExpand) {
                    header.classList.remove('collapsed');
                    content.classList.remove('hidden');
                } else {
                    header.classList.add('collapsed');
                    content.classList.add('hidden');
                }
            });
        }
    </script>
</body>
</html>
"""
    
    with open(output_path, 'w') as f:
        f.write(html_content)


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_html_report.py <input_report.txt> [output.html]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else input_path.replace('.txt', '.html')
    
    print(f"Parsing report: {input_path}")
    data = parse_text_report(input_path)
    
    print(f"Generating HTML report: {output_path}")
    generate_html_report(data, output_path)
    
    print(f"✅ HTML report generated successfully!")
    print(f"   Open {output_path} in your browser to view the report.")


if __name__ == '__main__':
    main()
