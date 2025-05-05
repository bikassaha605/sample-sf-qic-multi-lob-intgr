# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

# html_sanitizer.py

from bs4 import BeautifulSoup
from typing import Optional
import re
from logger import get_logger

logger = get_logger(__name__)

class HTMLSanitizer:
    """
    A class to handle HTML sanitization and formatting.
    """
    
    def __init__(self):
        """
        Initialize HTMLSanitizer with allowed attributes for specific tags.
        """
        self.allowed_table_attrs = ['border']
        self.allowed_link_attrs = ['href', 'title']
        self.allowed_img_attrs = ['src', 'alt', 'title']

    def sanitize_html(self, html_content: Optional[str]) -> str:
        """
        Performs basic HTML sanitization:
        - Removes style attributes
        - Removes unnecessary whitespace
        - Keeps basic structure and formatting
        - Preserves essential attributes for links and images
        
        Args:
            html_content (str): Raw HTML content
        Returns:
            str: Sanitized HTML content
        """
        if not html_content:
            return ""

        # Create BeautifulSoup object
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove style attributes from all tags
        for tag in soup.find_all():               
            # Remove target attributes from links
            if tag.name == 'a' and 'target' in tag.attrs:
                del tag['target']
                
            # Convert b tags to strong
            if tag.name == 'b':
                tag.name = 'strong'

        # Clean up tables
        for table in soup.find_all('table'):
            if 'border' in table.attrs:
                table['border'] = '1'
            # Remove other table attributes
            for attr in list(table.attrs):
                if attr not in self.allowed_table_attrs:
                    del table[attr]
                    
        # Clean up links
        for link in soup.find_all('a'):
            for attr in list(link.attrs):
                if attr not in self.allowed_link_attrs:
                    del link[attr]
                    
        # Clean up images
        for img in soup.find_all('img'):
            for attr in list(img.attrs):
                if attr not in self.allowed_img_attrs:
                    del img[attr]

        # Convert non-breaking spaces
        html_content = str(soup)
        html_content = html_content.replace('\xa0', ' ')
        html_content = html_content.replace('\n', ' ')

        return html_content
