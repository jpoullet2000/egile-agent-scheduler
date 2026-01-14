"""Output handler for saving job results.

This module handles saving job results in various formats (PDF, Markdown, HTML, etc.).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class OutputHandler:
    """Handles saving job results to files."""

    def __init__(self):
        """Initialize the output handler."""
        pass

    async def save_output(
        self,
        job_name: str,
        result: str,
        output_config: dict[str, Any],
    ) -> Path:
        """
        Save job result to file.

        Args:
            job_name: Name of the job
            result: Result content from agent/team
            output_config: Output configuration dictionary

        Returns:
            Path to the saved file
        """
        output_type = output_config["type"]
        output_path = output_config.get("path", "output")
        
        # Create output directory if needed
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = output_config.get("filename", f"{job_name}_{timestamp}")
        
        # Replace placeholders in filename
        base_filename = base_filename.replace('<date_timestamp>', timestamp)
        base_filename = base_filename.replace('<job_name>', job_name)
        
        # Save based on type
        if output_type == "pdf":
            filepath = await self._save_pdf(output_dir, base_filename, result, output_config)
        elif output_type == "markdown":
            filepath = await self._save_markdown(output_dir, base_filename, result)
        elif output_type == "html":
            filepath = await self._save_html(output_dir, base_filename, result)
        elif output_type == "json":
            filepath = await self._save_json(output_dir, base_filename, result)
        elif output_type == "text":
            filepath = await self._save_text(output_dir, base_filename, result)
        else:
            raise ValueError(f"Unknown output type: {output_type}")
        
        logger.info(f"Saved job '{job_name}' output to: {filepath}")
        return filepath

    async def _save_pdf(
        self,
        output_dir: Path,
        base_filename: str,
        content: str,
        output_config: dict,
    ) -> Path:
        """Save content as PDF."""
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        
        filepath = output_dir / f"{base_filename}.pdf"
        
        # Create PDF
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#1a1a1a',
            spaceAfter=30,
        )
        
        # Add title if configured
        title = output_config.get("title", "Agent Report")
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 12))
        
        # Add timestamp
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        elements.append(Paragraph(f"Generated: {timestamp}", styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Add content (convert markdown to paragraphs)
        for line in content.split('\n'):
            if line.strip():
                # Simple markdown to PDF conversion
                if line.startswith('# '):
                    elements.append(Paragraph(line[2:], styles['Heading1']))
                elif line.startswith('## '):
                    elements.append(Paragraph(line[3:], styles['Heading2']))
                elif line.startswith('### '):
                    elements.append(Paragraph(line[4:], styles['Heading3']))
                else:
                    elements.append(Paragraph(line, styles['BodyText']))
            else:
                elements.append(Spacer(1, 12))
        
        # Build PDF
        doc.build(elements)
        
        return filepath

    async def _save_markdown(
        self,
        output_dir: Path,
        base_filename: str,
        content: str,
    ) -> Path:
        """Save content as Markdown."""
        filepath = output_dir / f"{base_filename}.md"
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return filepath

    async def _save_html(
        self,
        output_dir: Path,
        base_filename: str,
        content: str,
    ) -> Path:
        """Save content as HTML."""
        filepath = output_dir / f"{base_filename}.html"
        
        # Simple HTML wrapper
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{base_filename}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1, h2, h3 {{ color: #1a1a1a; }}
        code {{ 
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="content">
        {self._markdown_to_html(content)}
    </div>
    <footer>
        <p><small>Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</small></p>
    </footer>
</body>
</html>"""
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)
        
        return filepath

    def _markdown_to_html(self, content: str) -> str:
        """Simple markdown to HTML conversion."""
        # This is a basic conversion - for production use a proper markdown library
        html_lines = []
        for line in content.split('\n'):
            if line.startswith('# '):
                html_lines.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith('## '):
                html_lines.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith('### '):
                html_lines.append(f"<h3>{line[4:]}</h3>")
            elif line.strip():
                html_lines.append(f"<p>{line}</p>")
            else:
                html_lines.append("<br>")
        return '\n'.join(html_lines)

    async def _save_json(
        self,
        output_dir: Path,
        base_filename: str,
        content: str,
    ) -> Path:
        """Save content as JSON."""
        filepath = output_dir / f"{base_filename}.json"
        
        # Wrap content in JSON structure
        data = {
            "timestamp": datetime.now().isoformat(),
            "content": content,
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath

    async def _save_text(
        self,
        output_dir: Path,
        base_filename: str,
        content: str,
    ) -> Path:
        """Save content as plain text."""
        filepath = output_dir / f"{base_filename}.txt"
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return filepath
