"""
Markdown renderer module for DocuMagnetIR Streamlit application.
Handles rendering of Mathpix Markdown content with mathematical notation using Node.js.
"""

import streamlit as st
from pathlib import Path
import sys
import os
import json
import re
import subprocess
import tempfile

# Add project root to path for imports
current_file = Path(__file__).resolve()
BASE_DIR = current_file.parent.parent

def find_mathpix_executable():
    """
    Find the mathpix-markdown-it executable within the virtual environment.
    
    Returns:
        str: Path to the executable or None if not found
    """
    # Get the Python executable path 
    python_path = sys.executable
    venv_path = Path(python_path).parent.parent
    
    # Possible locations for the npm binaries
    possible_paths = [
        # Node modules .bin location (most likely based on user's findings)
        venv_path / "Lib" / "site-packages" / "nodejs_wheel" / "node_modules" / ".bin" / "mathpix-markdown-it.cmd",
        venv_path / "Lib" / "site-packages" / "nodejs_wheel" / "node_modules" / ".bin" / "mathpix-markdown-it",
        # Lower case 'lib' version
        venv_path / "lib" / "site-packages" / "nodejs_wheel" / "node_modules" / ".bin" / "mathpix-markdown-it.cmd",
        venv_path / "lib" / "site-packages" / "nodejs_wheel" / "node_modules" / ".bin" / "mathpix-markdown-it",
        # Direct in the node_modules directory
        venv_path / "Lib" / "site-packages" / "nodejs_wheel" / "node_modules" / "mathpix-markdown-it" / "bin" / "mathpix-markdown-it.js",
        venv_path / "lib" / "site-packages" / "nodejs_wheel" / "node_modules" / "mathpix-markdown-it" / "bin" / "mathpix-markdown-it.js",
        # Standard npm global paths within virtual environment
        venv_path / "lib" / "site-packages" / "nodejs_wheel" / "bin" / "mathpix-markdown-it",
        venv_path / "lib" / "site-packages" / "nodejs_wheel" / "bin" / "mathpix-markdown-it.cmd",
        venv_path / "Lib" / "site-packages" / "nodejs_wheel" / "bin" / "mathpix-markdown-it",
        venv_path / "Lib" / "site-packages" / "nodejs_wheel" / "bin" / "mathpix-markdown-it.cmd",
        # Windows specific paths
        venv_path / "Scripts" / "mathpix-markdown-it.cmd",
        venv_path / "Scripts" / "mathpix-markdown-it",
        # NPX within virtual environment
        venv_path / "lib" / "site-packages" / "nodejs_wheel" / "bin" / "npx",
        venv_path / "lib" / "site-packages" / "nodejs_wheel" / "bin" / "npx.cmd",
        venv_path / "Lib" / "site-packages" / "nodejs_wheel" / "bin" / "npx",
        venv_path / "Lib" / "site-packages" / "nodejs_wheel" / "bin" / "npx.cmd",
        venv_path / "Scripts" / "npx.cmd",
        venv_path / "Scripts" / "npx",
    ]
    
    # Check which paths exist
    for path in possible_paths:
        if path.exists():
            return str(path)
            
    return None

def render_mathpix_markdown(text):
    """
    Render Mathpix Markdown text to HTML for display in Streamlit using Node.js.
    
    Args:
        text (str): The text containing Mathpix Markdown
    
    Returns:
        str: HTML representation of the rendered text
    """
    try:
        # Find the mathpix-markdown-it executable
        mathpix_path = find_mathpix_executable()
        
        # Create a temporary file to store the markdown content
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.md', delete=False, encoding='utf-8') as temp_md:
            temp_md.write(text)
            temp_md_path = temp_md.name
        
        # Create a temporary file for the output HTML
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp_html:
            temp_html_path = temp_html.name
            
        # Prepare command to convert markdown to HTML
        if mathpix_path:
            if mathpix_path.endswith('.js'):
                # For JS files, use node to execute them
                cmd = ['node', mathpix_path, temp_md_path, '--outfile', temp_html_path, '--include-math-css']
            elif 'npx' in mathpix_path:
                # If we found npx, use it to run mathpix-markdown-it
                cmd = [mathpix_path, 'mathpix-markdown-it', temp_md_path, '--outfile', temp_html_path, '--include-math-css']
            else:
                # Otherwise use the direct command
                cmd = [mathpix_path, temp_md_path, '--outfile', temp_html_path, '--include-math-css']
        else:
            # Fallback to just trying the command and hoping it's in PATH
            cmd = ['mathpix-markdown-it', temp_md_path, '--outfile', temp_html_path, '--include-math-css']
        
        # Print the command for debugging
        print(f"Running command: {' '.join(cmd)}")
        
        # Run the command
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            # If using the direct executable failed, try with Node directly if it's a JS file
            if mathpix_path and mathpix_path.endswith('.js'):
                # Already tried with node
                pass
            elif mathpix_path and (mathpix_path.endswith('.cmd') or not '.' in Path(mathpix_path).name):
                # Try to find the underlying JS file
                js_path = None
                node_modules = Path(mathpix_path).parent.parent
                if node_modules.name == '.bin':
                    possible_js = node_modules.parent / 'mathpix-markdown-it' / 'bin' / 'mathpix-markdown-it.js'
                    if possible_js.exists():
                        js_path = str(possible_js)
                
                if js_path:
                    cmd = ['node', js_path, temp_md_path, '--outfile', temp_html_path, '--include-math-css']
                    print(f"Retrying with node directly: {' '.join(cmd)}")
                    process = subprocess.run(cmd, capture_output=True, text=True)
            
            # If still failed, try with system-wide npx as a last resort
            if process.returncode != 0:
                cmd = ['npx', 'mathpix-markdown-it', temp_md_path, '--outfile', temp_html_path, '--include-math-css']
                print(f"Trying with npx: {' '.join(cmd)}")
                process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                # If that still failed, try using npm exec
                cmd = ['npm', 'exec', '--', 'mathpix-markdown-it', temp_md_path, '--outfile', temp_html_path, '--include-math-css']
                print(f"Trying with npm exec: {' '.join(cmd)}")
                process = subprocess.run(cmd, capture_output=True, text=True)
            
            if process.returncode != 0:
                # Still failed, display error and raw text
                error_msg = f"""
                <div style="background-color: #FFEB3B; color: #212121; padding: 10px; margin: 10px 0; border-radius: 4px;">
                    <strong>Warning:</strong> Error rendering with mathpix-markdown-it.<br>
                    <details>
                        <summary>View error details</summary>
                        <pre>{process.stderr}</pre>
                        <pre>Command: {' '.join(cmd)}</pre>
                    </details>
                </div>
                """
                return error_msg + f"<pre>{text}</pre>"
        
        # Read the generated HTML file
        with open(temp_html_path, 'r', encoding='utf-8') as html_file:
            html_content = html_file.read()
            
        # Extract the body content
        body_match = re.search(r'<body>(.*?)</body>', html_content, re.DOTALL)
        if body_match:
            html = body_match.group(1)
        else:
            html = html_content
            
        # Clean up temporary files
        try:
            os.unlink(temp_md_path)
            os.unlink(temp_html_path)
        except:
            pass
            
        # Apply custom styling for better integration with Streamlit
        styled_html = f"""
        <div class="mathpix-rendered">
            {html}
        </div>
        <style>
            .mathpix-rendered {{
                font-family: "Source Sans Pro", sans-serif;
                line-height: 1.6;
            }}
            .mathpix-rendered .katex {{
                font-size: 1.1em;
            }}
            .mathpix-rendered table {{
                border-collapse: collapse;
                margin: 1em 0;
                width: auto;
            }}
            .mathpix-rendered table td, .mathpix-rendered table th {{
                border: 1px solid #ddd;
                padding: 8px;
            }}
            .mathpix-rendered pre {{
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
            }}
            .mathpix-rendered img {{
                max-width: 100%;
            }}
        </style>
        """
        
        return styled_html
        
    except Exception as e:
        # If an error occurs, return a warning and the raw text
        warning = f"""
        <div style="background-color: #FFEB3B; color: #212121; padding: 10px; margin: 10px 0; border-radius: 4px;">
            <strong>Warning:</strong> Error rendering markdown: {str(e)}
        </div>
        """
        return warning + f"<pre>{text}</pre>"

def display_rendered_markdown(text):
    """
    Display Mathpix Markdown text in Streamlit with proper rendering.
    
    Args:
        text (str): The text containing Mathpix Markdown
    """
    rendered_html = render_mathpix_markdown(text)
    st.markdown(rendered_html, unsafe_allow_html=True)