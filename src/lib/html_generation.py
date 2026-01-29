def get_notes_markdown_css() -> str:
    """Return CSS for markdown-enabled notes (collapse + edit/preview)."""
    return '''
    .notes-container[data-mode] {
        position: relative;
        margin-top: 15px;
        padding: 12px;
        background: #f8f9fa;
        border-radius: 4px;
        border-left: 3px solid #6c757d;
        transition: box-shadow 0.2s;
    }
    .notes-header {
        display: flex;
        align-items: center;
        font-weight: 600;
        font-size: 1em;
        padding: 10px 16px;
        background: #eef1f4;
        border-bottom: 1px solid #e2e6ea;
        cursor: pointer;
        user-select: none;
    }
    .notes-title { flex: 1; color: #495057; }
    /* Slider toggle switch */
    .toggle-switch { display: inline-flex; align-items: center; margin-left: 10px; }
    .toggle-switch input.toggle-mode { position: absolute; opacity: 0; width: 0; height: 0; }
    .toggle-label { font-size: 0.85em; color: #606672; margin: 0 8px; user-select: none; }
    .toggle-slider { width: 44px; height: 24px; background: #e2e6ea; border-radius: 999px; display: inline-block; position: relative; transition: background 0.15s ease-in-out; vertical-align: middle; }
    .toggle-slider::before { content: ''; position: absolute; width: 18px; height: 18px; left: 3px; top: 3px; background: #fff; border-radius: 50%; box-shadow: 0 1px 2px rgba(0,0,0,0.15); transition: transform 0.15s ease-in-out; }
    .toggle-switch input.toggle-mode:checked + .toggle-slider { background: #667eea; }
    .toggle-switch input.toggle-mode:checked + .toggle-slider::before { transform: translateX(20px); }
    /* Highlight active label */
    .toggle-switch input.toggle-mode:checked ~ .toggle-label.toggle-label-preview { color: #0f172a; font-weight: 700; }
    .toggle-switch input.toggle-mode:not(:checked) ~ .toggle-label.toggle-label-edit { color: #0f172a; font-weight: 700; }
    /* Place edit and preview views in the same visual area so preview replaces the textarea */
        .notes-content { position: relative; margin-top: 8px; padding: 10px 0; }
    .note-edit, .note-preview { width: 100%; box-sizing: border-box; min-height: 96px; padding: 10px; margin: 0; }
    .note-field { display: block; }
    .notes-container[data-mode="edit"] .note-edit { display: block; }
    .notes-container[data-mode="edit"] .note-preview { display: none; }
    .notes-container[data-mode="preview"] .note-preview { display: block; }
        .note-preview { background: #fff; border: 1px solid #ced4da; border-radius: 4px; color: #222; font-size: 1em; line-height: 1.6; }
        /* Removed broad .note-edit hide rules so question/answer can be targeted separately */

        /* Make preview sit on the container background (transparent) so header/lists align with .notes-container */
        .notes-container .note-preview {
            width: 100%;
            box-sizing: border-box;
            /* transparent so the gray container shows through */
            background: transparent;
            border: none;
            padding: 0;
            min-height: 0;
        }
        /* Remove default markdown spacing so header + lists align with surrounding UI */
        .notes-container .note-preview > :first-child { margin-top: 0; }
        .notes-container .note-preview > :last-child { margin-bottom: 0; }
        .notes-container .note-preview ul,
        .notes-container .note-preview ol { margin: 0; padding-left: 1.25rem; }
        /* Nuclear hide rule: make textarea hiding unavoidably specific */
        /* Hide only the Question textarea (IDs prefixed with note-q-) when previewing; leave Answer editable */
        /* Strong rules to hide and disable question textarea in preview mode */
        details.notes-container[data-mode="preview"] textarea[id^="note-q-"],
        details.notes-container[data-mode="preview"] textarea.note-question,
        details.notes-container[data-mode="preview"] .note-question textarea.note-field,
        details.notes-container[data-mode="preview"] .notes-content > textarea[id^="note-q-"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            border: 0 !important;
            overflow: hidden !important;
            pointer-events: none !important;
        }

        /* Default: preview hidden until preview mode */
        details.notes-container .note-preview { display: none; }
        details.notes-container[data-mode="preview"] .note-preview { display: block; }

        /* Tighten markdown spacing */
        details.notes-container .note-preview > :first-child { margin-top: 0; }
        details.notes-container .note-preview > :last-child { margin-bottom: 0; }
        details.notes-container .note-preview ul,
        details.notes-container .note-preview ol { margin: 0; padding-left: 1.25rem; }
    /* Removed legacy broad nesting rule for textarea hiding; question-only rules are applied instead */
    /* Labels remain visible in preview; only textareas are hidden via stronger rules above */
    .note-preview h1, .note-preview h2, .note-preview h3, .note-preview h4, .note-preview h5, .note-preview h6 {
        margin: 0 0 0.5em 0;
        font-weight: 700;
        line-height: 1.2;
    }
    .note-preview h1 { font-size: 1.5em; border-bottom: 1px solid #e2e6ea; }
    .note-preview h2 { font-size: 1.3em; border-bottom: 1px solid #e2e6ea; }
    .note-preview h3 { font-size: 1.1em; }
    .note-preview code, .note-preview pre {
        font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace;
        background: #f3f3f3;
        border-radius: 3px;
        padding: 2px 6px;
        font-size: 0.97em;
    }
    .note-preview pre { padding: 10px; overflow-x: auto; margin: 0.75em 0; }
    /* Normalize list alignment inside preview so bullets line up with headings */
    .note-preview ul, .note-preview ol { margin: 0; padding-left: 1.25rem; }
    .note-preview li { margin: 0.35rem 0; }
    .note-warning { display: flex; align-items: center; color: #b85c00; background: #fffbe6; border: 1px solid #ffe58f; border-radius: 3px; padding: 6px 10px; margin: 8px 0; }
    .notes-container { border: 1px solid #d0d7de; border-radius: 6px; margin: 1em 0; background: #f9f9fb; box-shadow: 0 1px 2px rgba(0,0,0,0.03); transition: box-shadow 0.2s; overflow: hidden; padding: 12px; }
    .notes-container[open] { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    .notes-container summary.notes-header { list-style: none; }
    .notes-container summary.notes-header::-webkit-details-marker { display: none; }
    .notes-container summary.notes-header::before { content: '\\25BC'; display: inline-block; margin-right: 0.5em; }
    .notes-container:not([open]) summary.notes-header::before { content: '\\25B6'; }
    @media (max-width: 768px) { .notes-header, .note-preview { font-size: 0.97em; } }
    '''


def get_notes_markdown_javascript() -> str:
    """Return JavaScript for markdown notes: render, toggle, init, collapse state."""
    return '''
    // Requires marked.js and DOMPurify via CDN (but graceful if missing)
    function renderMarkdown(rawMarkdown) {
        let dirtyHtml = '';
        let cleanHtml = '';
        let hasInvalidSyntax = false;

        function escapeHtml(str) {
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }

        try {
            if (typeof marked === 'undefined' || typeof DOMPurify === 'undefined') {
                // Markdown engine not present — fall back to escaped text preserving line breaks
                // Use RegExp constructor to avoid emitting regex literal slashes that can be split
                dirtyHtml = escapeHtml(rawMarkdown || '').replace(new RegExp('\\\\n','g'), '<br>');
                cleanHtml = dirtyHtml;
            } else {
                dirtyHtml = marked.parse(rawMarkdown || '');
                cleanHtml = DOMPurify.sanitize(dirtyHtml, {ALLOWED_TAGS: ['h1','h2','h3','h4','h5','h6','p','ul','ol','li','pre','code','blockquote','strong','em','a','hr','br','span','img'], ALLOWED_ATTR: ['href','src','alt','title','target'], FORCE_BODY: true});
            }
        } catch (e) {
            // If parsing fails, treat as invalid markdown but show escaped content
            hasInvalidSyntax = true;
            cleanHtml = escapeHtml(rawMarkdown || '');
        }

        return {rawMarkdown, dirtyHtml, cleanHtml, hasInvalidSyntax};
    }

    function toggleNoteMode(event, resource, attribute) {
        try { if (event && event.stopPropagation) event.stopPropagation(); } catch (e) {}
        // Try to find container via event, fall back to data attributes
        let container = null;
        try {
            if (event && event.target) container = event.target.closest('.notes-container');
        } catch (e) {}
        if (!container) container = document.querySelector(`.notes-container[data-resource="${resource}"][data-attribute="${attribute}"]`);
        if (!container) return;
        const mode = container.getAttribute('data-mode');
        // Flip mode
        const newMode = mode === 'edit' ? 'preview' : 'edit';
        container.setAttribute('data-mode', newMode);
        // Ensure question textareas are readonly/disabled in preview mode as a JS-level fallback
        try {
            if (newMode === 'preview') {
                container.querySelectorAll('textarea.note-question, textarea[id^="note-q-"]').forEach(function(t) {
                    try { t.setAttribute('readonly', 'true'); t.setAttribute('aria-hidden', 'true'); t.style.pointerEvents = 'none'; } catch (e) {}
                });
            } else {
                container.querySelectorAll('textarea.note-question, textarea[id^="note-q-"]').forEach(function(t) {
                    try { t.removeAttribute('readonly'); t.removeAttribute('aria-hidden'); t.style.pointerEvents = 'auto'; } catch (e) {}
                });
            }
        } catch (e) {}
        // When moving to preview, render ALL note content blocks (question + answer)
        if (newMode === 'preview') {
            container.querySelectorAll('.notes-content').forEach(function(block) {
                const textarea = block.querySelector('.note-edit');
                const preview = block.querySelector('.note-preview');
                if (textarea && preview) {
                    const result = renderMarkdown(textarea.value);
                    preview.innerHTML = result.cleanHtml;
                    let warning = block.querySelector('.note-warning');
                    if (result.hasInvalidSyntax) {
                        if (!warning) {
                            warning = document.createElement('div');
                            warning.className = 'note-warning';
                            warning.innerHTML = '<span class="note-warning-icon" aria-hidden="true">⚠️</span> <strong>Malformed Markdown:</strong> Preview may be incomplete.';
                            preview.parentNode.insertBefore(warning, preview);
                        }
                    } else if (warning) {
                        warning.remove();
                    }
                }
            });
        }
        // Update the toggle control (checkbox slider) aria state
        const toggleBtn = container.querySelector('.toggle-mode');
        if (toggleBtn) {
            try {
                if (toggleBtn.tagName === 'INPUT') {
                    toggleBtn.checked = (newMode === 'preview');
                    toggleBtn.setAttribute('aria-checked', newMode === 'preview' ? 'true' : 'false');
                } else {
                    toggleBtn.setAttribute('aria-pressed', newMode === 'edit' ? 'true' : 'false');
                }
            } catch (e) {}
        }
    }

    function initializeNoteMode(reportId, resource, attribute) {
        const container = document.querySelector(`.notes-container[data-resource="${resource}"][data-attribute="${attribute}"]`);
        if (!container) return;
        const textarea = container.querySelector('.note-edit');
        const preview = container.querySelector('.note-preview');
        let hasContent = false;
        if (textarea && textarea.value.trim().length > 0) hasContent = true;
        if (hasContent) {
            container.setAttribute('data-mode', 'preview');
            // make question textarea readonly when initializing in preview mode
            try { container.querySelectorAll('textarea.note-question, textarea[id^="note-q-"]').forEach(function(t){ try { t.setAttribute('readonly','true'); t.style.pointerEvents='none'; } catch(e){} }); } catch(e) {}
            if (preview && textarea) {
                const result = renderMarkdown(textarea.value);
                preview.innerHTML = result.cleanHtml;
            }
            // Update toggle button label when initializing in preview mode
            const toggleBtnInit = container.querySelector('.toggle-mode');
            if (toggleBtnInit) {
                try { if (toggleBtnInit.tagName === 'INPUT') { toggleBtnInit.checked = true; toggleBtnInit.setAttribute('aria-checked', 'true'); } else { toggleBtnInit.setAttribute('aria-pressed','false'); toggleBtnInit.textContent='Edit'; } } catch(e) {}
            }
            // visibility is driven by data-mode and CSS; avoid inline styles
        } else {
            container.setAttribute('data-mode', 'edit');
            // ensure question textarea editable in edit mode
            try { container.querySelectorAll('textarea.note-question, textarea[id^="note-q-"]').forEach(function(t){ try { t.removeAttribute('readonly'); t.style.pointerEvents='auto'; } catch(e){} }); } catch(e) {}
            if (preview) preview.innerHTML = '';
            const toggleBtnInit = container.querySelector('.toggle-mode');
            if (toggleBtnInit) {
                try { if (toggleBtnInit.tagName === 'INPUT') { toggleBtnInit.checked = false; toggleBtnInit.setAttribute('aria-checked', 'false'); } else { toggleBtnInit.setAttribute('aria-pressed','true'); toggleBtnInit.textContent='Preview'; } } catch(e) {}
            }
            // visibility is driven by data-mode and CSS; avoid inline styles
        }
    }

    function saveCollapseState(resource, attribute, isCollapsed) {
        const reportId = window.getReportId ? window.getReportId() : 'unknown-report';
        const key = `tf-notes-${reportId}#${resource}#${attribute}`;
        let note = {};
        try { const existing = localStorage.getItem(key); if (existing) note = JSON.parse(existing); } catch (e) {}
        note.isCollapsed = isCollapsed;
        try { localStorage.setItem(key, JSON.stringify(note)); } catch (e) {}
    }

    function restoreCollapseState(reportId, resource, attribute) {
        const key = `tf-notes-${reportId}#${resource}#${attribute}`;
        let note = {};
        try { const existing = localStorage.getItem(key); if (existing) note = JSON.parse(existing); } catch (e) {}
        return note.isCollapsed === true;
    }

    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('.notes-container').forEach(function(container) {
            const resource = container.getAttribute('data-resource');
            const attribute = container.getAttribute('data-attribute');
            const reportId = window.getReportId ? window.getReportId() : 'unknown-report';
            const isCollapsed = restoreCollapseState(reportId, resource, attribute);
            if (isCollapsed) { container.removeAttribute('open'); const summary = container.querySelector('summary.notes-header'); if (summary) summary.setAttribute('data-collapsed', 'true'); }
            else { container.setAttribute('open', 'open'); const summary = container.querySelector('summary.notes-header'); if (summary) summary.setAttribute('data-collapsed', 'false'); }
            container.addEventListener('toggle', function(e) { const isNowCollapsed = !container.hasAttribute('open'); saveCollapseState(resource, attribute, isNowCollapsed); const summary = container.querySelector('summary.notes-header'); if (summary) summary.setAttribute('data-collapsed', isNowCollapsed ? 'true' : 'false'); });
        });
    });

    function saveNoteWithBlur(resource, attribute, field, el) {
        if (!window.saveNote) return;
        try {
            // If caller provided the element, use it
            if (el && typeof el.value !== 'undefined') {
                window.saveNote(resource, attribute, field, el.value);
                return;
            }

            // Fallback: construct the canonical textarea id used by the generator
            // sanitized names replace . [ ] : with '-'
            function sanitizeName(name) { return String(name).replace(/[.\[\]:]/g, '-'); }
            const sRes = sanitizeName(resource);
            const sAttr = sanitizeName(attribute);
            const prefix = (field === 'question') ? 'q' : (field === 'answer' ? 'a' : '');
            if (prefix) {
                const id = `note-${prefix}-${sRes}-${sAttr}`;
                const node = document.getElementById(id);
                if (node && typeof node.value !== 'undefined') {
                    window.saveNote(resource, attribute, field, node.value);
                    return;
                }
            }

            // Last resort: find the textarea inside the notes-container for this resource/attribute
            const fallback = document.querySelector(`.notes-container[data-resource="${resource}"][data-attribute="${attribute}"] textarea.note-field`);
            if (fallback && typeof fallback.value !== 'undefined') {
                window.saveNote(resource, attribute, field, fallback.value);
            }
        } catch (e) {}
    }
    
    // Expose handlers to global scope so inline `onclick`/`onblur` attributes work
    try {
        window.renderMarkdown = renderMarkdown;
        window.toggleNoteMode = toggleNoteMode;
        window.initializeNoteMode = initializeNoteMode;
        window.saveNoteWithBlur = saveNoteWithBlur;
        window.saveCollapseState = saveCollapseState;
        window.restoreCollapseState = restoreCollapseState;
    } catch (e) {}
    '''
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
        
        /* Tooltip styling for ignored attributes badge */
        .resource-change-header {
            overflow: visible !important;
        }
        
        .badge[data-tooltip] {
            position: relative;
            cursor: help;
        }
        
        .badge[data-tooltip]:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: calc(100% + 10px);
            left: 50%;
            transform: translateX(-50%);
            padding: 8px 12px;
            background: #1f2937;
            color: white;
            font-size: 0.85em;
            font-weight: normal;
            border-radius: 6px;
            white-space: pre;
            text-align: left;
            z-index: 99999;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            pointer-events: none;
        }
        
        .badge[data-tooltip]:hover::before {
            content: '';
            position: absolute;
            bottom: calc(100% + 4px);
            left: 50%;
            transform: translateX(-50%);
            border: 6px solid transparent;
            border-top-color: #1f2937;
            z-index: 99999;
            pointer-events: none;
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
            display: inline;
        }
        
        .baseline-added {
            background-color: #c8e6c9;
            color: #1b5e20;
            display: inline;
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
            overflow: visible;
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
            flex: 1 1 0;
            min-width: 0;
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
        
        .json-sort-control {
            float: right;
            font-size: 0.85em;
            padding: 4px 8px;
            border: 1px solid #667eea;
            border-radius: 4px;
            background: white;
            color: #667eea;
            cursor: pointer;
            transition: all 0.2s;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .json-sort-control:hover {
            background: #667eea;
            color: white;
        }
        
        .json-sort-control:focus {
            outline: 2px solid #667eea;
            outline-offset: 2px;
        }
"""


def get_scrollable_container_css() -> str:
    """
    Get CSS for scrollable value containers.

    Prevents layout breakage from large JSON objects or long strings
    by adding scrollbars when content exceeds thresholds.

    Returns:
        str: CSS stylesheet for scrollable containers including:
            - .value-container: Scrollable wrapper with max dimensions
            - Webkit scrollbar styling for better UX

    Example:
        >>> css = get_scrollable_container_css()
        >>> "max-height: 400px" in css
        True
    """
    return """
        .value-container {
            max-width: 600px;
            overflow-x: auto;
            padding: 8px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        
        .value-container pre,
        .value-container pre pre {
            white-space: pre;
            overflow-wrap: normal;
            word-wrap: normal;
            word-break: normal;
            margin: 0;
            overflow: visible;
            max-width: none;
        }
        
        .value-container code {
            white-space: pre;
            overflow-wrap: normal;
            word-wrap: normal;
            word-break: normal;
            margin: 0;
            display: block;
            overflow: visible;
            max-width: none;
        }
        
        /* Webkit scrollbar styling for better UX */
        .value-container::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        .value-container::-webkit-scrollbar-track {
            background: #e9ecef;
            border-radius: 4px;
        }
        
        .value-container::-webkit-scrollbar-thumb {
            background: #adb5bd;
            border-radius: 4px;
        }
        
        .value-container::-webkit-scrollbar-thumb:hover {
            background: #868e96;
        }
"""


def get_sticky_header_css() -> str:
    """
    Get CSS for sticky environment headers.

    Keeps environment column headers visible when scrolling vertically
    through attribute sections.

    Returns:
        str: CSS stylesheet for sticky headers including:
            - .env-headers: Container for environment header row
            - .env-header: Individual environment label
            - .sticky-header: Position sticky styling

    Example:
        >>> css = get_sticky_header_css()
        >>> "position: sticky" in css
        True
    """
    return """
        .env-headers {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 20px;
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        
        .env-header {
            flex: 1;
            min-width: 250px;
            font-weight: 700;
            font-size: 1.1em;
            color: #667eea;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 4px;
            text-align: center;
        }
        
        .sticky-header {
            position: sticky;
            top: 0;
            z-index: 10;
            background: white;
        }
"""


def get_env_specific_section_css() -> str:
    """
    Get CSS for environment-specific resource grouping section.

    Provides styling for collapsible <details> section that groups resources
    existing in only some environments (not all).

    Returns:
        str: CSS stylesheet for environment-specific sections including:
            - .env-specific-section: Details element container
            - .env-specific-header: Summary element with warning styling
            - .env-specific-badge: Amber warning badge showing affected envs
            - .resource-count: Badge showing number of env-specific resources
            - .presence-info: Shows "Present in" and "Missing from" lists

    Example:
        >>> css = get_env_specific_section_css()
        >>> ".env-specific-section" in css
        True
    """
    return """
        .env-specific-section {
            margin-top: 30px;
            border: 2px solid #ffa94d;
            border-radius: 8px;
            background: #fff4e6;
        }
        
        .env-specific-header {
            padding: 15px 20px;
            font-size: 1.2em;
            font-weight: 600;
            color: #e67700;
            cursor: pointer;
            user-select: none;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .env-specific-header:hover {
            background: #ffe8cc;
        }
        
        .env-specific-header::marker {
            content: "▼ ";
            font-size: 0.8em;
        }
        
        details.env-specific-section:not([open]) .env-specific-header::marker {
            content: "▶ ";
        }
        
        .env-specific-badge {
            background: #ffa94d;
            color: #7d4400;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
            display: inline-block;
        }
        
        .resource-count {
            background: #e67700;
            color: white;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 600;
            margin-left: auto;
        }
        
        .presence-info {
            padding: 10px 15px;
            background: #fff;
            border-radius: 4px;
            margin: 10px 0;
            border-left: 3px solid #ffa94d;
        }
        
        .presence-info strong {
            color: #495057;
            display: block;
            margin-bottom: 5px;
        }
        
        .presence-info ul {
            margin: 5px 0 5px 20px;
            color: #666;
        }
        
        .env-specific-content {
            padding: 0 20px 20px 20px;
        }
"""


def get_first_env_only_section_css() -> str:
    """
    Get CSS for first-environment-only resource grouping section.

    Provides styling for collapsible <details> section that groups resources
    existing only in the first (baseline) environment that will be created in others.

    Returns:
        str: CSS stylesheet for first-env-only sections including:
            - .first-env-only-section: Details element container with green theme
            - .first-env-only-header: Summary element with success styling
            - .first-env-badge: Green badge showing where resources will be created
            - .first-env-only-content: Content container

    Example:
        >>> css = get_first_env_only_section_css()
        >>> ".first-env-only-section" in css
        True
    """
    return """
        .first-env-only-section {
            margin-top: 30px;
            margin-bottom: 30px;
            border: 2px solid #10b981;
            border-radius: 8px;
            background: #d1fae5;
        }
        
        .first-env-only-header {
            padding: 15px 20px;
            font-size: 1.2em;
            font-weight: 600;
            color: #065f46;
            cursor: pointer;
            user-select: none;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .first-env-only-header:hover {
            background: #a7f3d0;
        }
        
        .first-env-only-header::marker {
            content: "▼ ";
            font-size: 0.8em;
        }
        
        details.first-env-only-section:not([open]) .first-env-only-header::marker {
            content: "▶ ";
        }
        
        .first-env-badge {
            background: #10b981;
            color: white;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .first-env-only-content {
            padding: 0 20px 20px 20px;
        }
"""


def get_notes_css() -> str:
    """
    Get CSS for attribute notes (question/answer fields).

    Returns:
        str: CSS stylesheet for notes functionality including:
            - Notes container styling with subtle background
            - Label typography for question/answer fields
            - Textarea styling with consistent sizing
            - Focus states and accessibility

    Example:
        >>> css = get_notes_css()
        >>> ".notes-container" in css
        True
        >>> ".note-field" in css
        True
    """
    return """
        .notes-container {
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
            border-left: 3px solid #6c757d;
        }
        
        .note-label {
            display: block;
            font-weight: 600;
            color: #495057;
            margin-bottom: 5px;
            font-size: 0.9em;
        }
        
        .note-field {
            width: 100%;
            padding: 10px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            font-size: 0.95em;
            line-height: 1.5;
            resize: vertical;
            background: white;
            transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
        }
        
        .note-field:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .note-field::placeholder {
            color: #adb5bd;
            font-style: italic;
        }
        
        .note-answer {
            margin-top: 12px;
        }
"""


def get_notes_javascript() -> str:
    """
    Get JavaScript for client-side notes functionality.

    Returns:
        str: Complete JavaScript code including:
            - getReportId(): Extract report filename from URL
            - debounce(func, delay): Debouncing utility for auto-save
            - saveNote(resource, attribute, field, value): Save note to LocalStorage
            - debouncedSaveNote: Debounced version of saveNote (500ms delay)
            - loadNotes(): Load all notes from LocalStorage on page load

    Example:
        >>> js = get_notes_javascript()
        >>> "function getReportId()" in js
        True
        >>> "localStorage.setItem" in js
        True
    """
    return """
        function getReportId() {
            const path = window.location.pathname;
            const filename = path.substring(path.lastIndexOf('/') + 1);
            return filename || 'unknown-report';
        }
        
        function debounce(func, delay) {
            let timeoutId;
            return function(...args) {
                clearTimeout(timeoutId);
                timeoutId = setTimeout(() => func.apply(this, args), delay);
            };
        }
        
        function saveNote(resourceAddress, attributeName, field, value) {
            const reportId = getReportId();
            const key = `tf-notes-${reportId}#${resourceAddress}#${attributeName}`;
            
            // Load existing note or create new one
            let note = {};
            try {
                const existing = localStorage.getItem(key);
                if (existing) {
                    note = JSON.parse(existing);
                }
            } catch (e) {
                console.error('Error loading note:', e);
            }
            
            // Update field
            note[field] = value;
            note.lastModified = Date.now();
            
            // Save to LocalStorage
            try {
                localStorage.setItem(key, JSON.stringify(note));
            } catch (e) {
                if (e.name === 'QuotaExceededError') {
                    console.error('LocalStorage quota exceeded. Cannot save note.');
                } else {
                    console.error('Error saving note:', e);
                }
            }
        }
        
        const debouncedSaveNote = debounce(saveNote, 500);
        
        function loadNotes() {
            const reportId = getReportId();
            const prefix = `tf-notes-${reportId}#`;
            
            // Iterate over all LocalStorage keys
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (!key || !key.startsWith(prefix)) continue;
                
                // Parse resource and attribute from key
                const keyParts = key.substring(prefix.length).split('#');
                if (keyParts.length !== 2) continue;
                
                const resourceAddress = keyParts[0];
                const attributeName = keyParts[1];
                
                // Sanitize for HTML ID (same as Python _sanitize_for_html_id)
                const sanitizedResource = resourceAddress.replace(/[.\\[\\]:]/g, '-');
                const sanitizedAttribute = attributeName.replace(/[.\\[\\]:]/g, '-');
                
                // Load note data
                try {
                    const noteData = JSON.parse(localStorage.getItem(key));
                    
                    // Populate question field
                    if (noteData.question) {
                        const questionField = document.getElementById(`note-q-${sanitizedResource}-${sanitizedAttribute}`);
                        if (questionField) {
                            questionField.value = noteData.question;
                        }
                    }
                    
                    // Populate answer field
                    if (noteData.answer) {
                        const answerField = document.getElementById(`note-a-${sanitizedResource}-${sanitizedAttribute}`);
                        if (answerField) {
                            answerField.value = noteData.answer;
                        }
                    }
                } catch (e) {
                    console.error(`Error loading note for ${key}:`, e);
                }
            }
        }
        
        // Load notes when page loads
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', loadNotes);
        } else {
            loadNotes();
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
    - Scrollable value containers (get_scrollable_container_css)
    - Sticky environment headers (get_sticky_header_css)

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
{get_scrollable_container_css()}
{get_sticky_header_css()}
{get_env_specific_section_css()}
{get_first_env_only_section_css()}
{get_notes_css()}
</style>"""
