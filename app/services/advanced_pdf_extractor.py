"""
Advanced PDF content extractor using PyMuPDF capabilities.
Handles text, tables, images, and structured content extraction.
"""
import fitz  # PyMuPDF
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import base64
from io import BytesIO


class AdvancedPDFExtractor:
    """Extracts structured content from PDFs including text, tables, and images."""

    def __init__(self):
        """Initialize the extractor."""
        # Only match actual question patterns (letters, Question X, Problem X, etc.)
        # Exclude simple numbered items (1., 2., etc.) which are usually scenario/context
        self.question_patterns = [
            r'^([a-z][\.\)]\s+)',  # a. or a) - actual sub-questions
            r'^([A-Z][\.\)]\s+)',  # A. or A) - actual sub-questions
            r'^(Question\s+\d+)',  # Question 1
            r'^(Problem\s+\d+)',  # Problem 1
            r'^(Exercise\s+\d+)',  # Exercise 1
        ]

    def extract_structured_content(self, pdf_path: str) -> Dict:
        """
        Extract all structured content from a PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dictionary with structured content
        """
        doc = fitz.open(pdf_path)

        structured_content = {
            'filename': Path(pdf_path).name,
            'pages': [],
            'questions': [],
            'tables': [],
            'images': [],
            'scenarios': [],
            'full_text': '',
        }

        all_text = []

        for page_num in range(len(doc)):
            page = doc[page_num]

            # Extract page content
            page_content = self._extract_page_content(page, page_num)
            structured_content['pages'].append(page_content)

            # Accumulate text
            all_text.append(page_content['text'])

        doc.close()

        # Combine all text
        structured_content['full_text'] = '\n\n'.join(all_text)

        # Identify scenarios FIRST (paragraphs before questions)
        structured_content['scenarios'] = self._identify_scenarios(structured_content)

        # Parse questions from full text (will use scenarios for enhancement)
        structured_content['questions'] = self._parse_questions(structured_content)

        return structured_content

    def _extract_page_content(self, page, page_num: int) -> Dict:
        """
        Extract all content from a single page.

        Args:
            page: PyMuPDF page object
            page_num: Page number

        Returns:
            Dictionary with page content
        """
        content = {
            'page_number': page_num + 1,
            'text': '',
            'blocks': [],
            'tables': [],
            'images': [],
        }

        # Extract text blocks with positioning
        blocks = page.get_text("dict")["blocks"]

        text_parts = []
        for block_num, block in enumerate(blocks):
            if block['type'] == 0:  # Text block
                block_text = ""
                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                    block_text += line_text + "\n"

                if block_text.strip():
                    content['blocks'].append({
                        'block_num': block_num,
                        'text': block_text.strip(),
                        'bbox': block.get('bbox'),
                    })
                    text_parts.append(block_text.strip())

            elif block['type'] == 1:  # Image block
                content['images'].append({
                    'block_num': block_num,
                    'bbox': block.get('bbox'),
                })

        content['text'] = '\n\n'.join(text_parts)

        # Extract tables using PyMuPDF
        try:
            tables = page.find_tables()
            for table_num, table in enumerate(tables):
                table_data = self._extract_table_data(table)
                if table_data:
                    content['tables'].append({
                        'table_num': table_num,
                        'data': table_data,
                        'bbox': table.bbox,
                        'page': page_num + 1,
                    })
        except:
            pass  # Tables might not be available in all PyMuPDF versions

        # Extract images
        image_list = page.get_images()
        for img_num, img in enumerate(image_list):
            xref = img[0]
            content['images'].append({
                'img_num': img_num,
                'xref': xref,
                'page': page_num + 1,
            })

        return content

    def _extract_table_data(self, table) -> Optional[List[List[str]]]:
        """
        Extract table data from PyMuPDF table object.

        Args:
            table: PyMuPDF table object

        Returns:
            2D list of table cells
        """
        try:
            return table.extract()
        except:
            return None

    def _parse_questions(self, structured_content: Dict) -> List[Dict]:
        """
        Parse questions from structured content.

        Args:
            structured_content: Structured content dictionary

        Returns:
            List of question dictionaries
        """
        questions = []
        full_text = structured_content['full_text']

        # Split by common question patterns
        lines = full_text.split('\n')

        current_question = None
        current_text = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line starts with a question marker
            is_question_start = False
            question_id = None

            for pattern in self.question_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    is_question_start = True
                    question_id = match.group(1).strip()
                    break

            if is_question_start:
                # Save previous question
                if current_question and current_text:
                    current_question['text'] = '\n'.join(current_text)
                    questions.append(current_question)

                # Start new question
                current_question = {
                    'id': question_id,
                    'full_line': line,
                    'text': '',
                    'has_scenario': False,
                    'has_table': False,
                    'has_image': False,
                }
                current_text = [line]

            elif current_question:
                current_text.append(line)

        # Save last question
        if current_question and current_text:
            current_question['text'] = '\n'.join(current_text)
            questions.append(current_question)

        # Enhance questions with context
        for question in questions:
            self._enhance_question_context(question, structured_content)

        return questions

    def _enhance_question_context(self, question: Dict, structured_content: Dict):
        """
        Enhance question with context about tables, images, scenarios based on PDF structure.

        Args:
            question: Question dictionary
            structured_content: Full structured content
        """
        # Check if there are actual TABLES extracted from PDF
        all_tables = []
        for page in structured_content['pages']:
            all_tables.extend(page.get('tables', []))

        if len(all_tables) > 0:
            question['has_table'] = True

        # Check if there are actual IMAGES extracted from PDF
        all_images = []
        for page in structured_content['pages']:
            all_images.extend(page.get('images', []))

        if len(all_images) > 0:
            question['has_image'] = True

        # Check if there's a SCENARIO (long paragraph before questions)
        # A scenario is typically a text block > 200 chars that appears before questions
        if len(structured_content.get('scenarios', [])) > 0:
            question['has_scenario'] = True

    def _identify_scenarios(self, structured_content: Dict) -> List[Dict]:
        """
        Identify scenario paragraphs (context before questions).

        Args:
            structured_content: Structured content

        Returns:
            List of scenario dictionaries
        """
        scenarios = []

        for page_content in structured_content['pages']:
            blocks = page_content['blocks']

            for i, block in enumerate(blocks):
                text = block['text']

                # Look for scenario indicators
                if self._is_scenario_block(text):
                    # Get next few blocks as they might be part of scenario
                    scenario_text = [text]
                    j = i + 1
                    while j < len(blocks) and j < i + 3:
                        next_block = blocks[j]['text']
                        if not self._is_question_start(next_block):
                            scenario_text.append(next_block)
                        else:
                            break
                        j += 1

                    scenarios.append({
                        'text': '\n\n'.join(scenario_text),
                        'page': page_content['page_number'],
                        'block_num': block['block_num'],
                    })

        return scenarios

    def _is_scenario_block(self, text: str) -> bool:
        """Check if text block is likely a scenario based on PDF structure."""
        text_lower = text.lower()

        scenario_indicators = [
            'following scenario',
            'case study',
            'consider the following',
            'given the following',
            'background:',
            'context:',
            'scenario:',
        ]

        # Check for explicit indicators
        for indicator in scenario_indicators:
            if indicator in text_lower:
                return True

        # Check if it's a numbered item (1., 2., etc.) which are usually scenario/transaction descriptions
        import re
        if re.match(r'^\d+[\.\)]\s+', text.strip()):
            return True

        # Check if it's a longer paragraph (likely context) and not a lettered question
        if len(text) > 200 and not self._is_question_start(text):
            return True

        return False

    def _is_question_start(self, text: str) -> bool:
        """Check if text starts with a question marker."""
        for pattern in self.question_patterns:
            if re.match(pattern, text.strip(), re.IGNORECASE):
                return True
        return False

    def extract_images(self, pdf_path: str, output_dir: Optional[str] = None) -> List[Dict]:
        """
        Extract all images from PDF and optionally save them.

        Args:
            pdf_path: Path to PDF
            output_dir: Directory to save images (optional)

        Returns:
            List of image information dictionaries
        """
        doc = fitz.open(pdf_path)
        images_info = []

        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)

                if base_image:
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    # Create image info
                    img_info = {
                        'page': page_num + 1,
                        'index': img_index,
                        'xref': xref,
                        'extension': image_ext,
                        'size': len(image_bytes),
                    }

                    # Save image if output directory provided
                    if output_dir:
                        image_filename = f"page{page_num + 1}_img{img_index}.{image_ext}"
                        image_path = output_path / image_filename
                        with open(image_path, "wb") as f:
                            f.write(image_bytes)
                        img_info['saved_path'] = str(image_path)
                    else:
                        # Store as base64 if not saving to disk
                        img_info['base64'] = base64.b64encode(image_bytes).decode('utf-8')

                    images_info.append(img_info)

        doc.close()
        return images_info

    def create_question_chunks(self, structured_content: Dict) -> List[Dict]:
        """
        Create intelligent chunks for vector storage.
        Each chunk represents a complete question with its context.

        Args:
            structured_content: Structured content from PDF

        Returns:
            List of chunk dictionaries ready for vector store
        """
        chunks = []

        # Create chunks for each question with full context
        for question in structured_content['questions']:
            chunk_text_parts = []

            # Add question text
            chunk_text_parts.append(f"Question: {question['text']}")

            # Find and add relevant scenario
            scenario_text = self._find_relevant_scenario(
                question,
                structured_content['scenarios']
            )
            if scenario_text:
                chunk_text_parts.insert(0, f"Context/Scenario:\n{scenario_text}")

            # Find and add relevant table
            table_text = self._find_relevant_table(
                question,
                structured_content
            )
            if table_text:
                chunk_text_parts.insert(1 if scenario_text else 0, f"Table:\n{table_text}")

            # Combine into chunk
            chunk = {
                'text': '\n\n'.join(chunk_text_parts),
                'metadata': {
                    'type': 'question',
                    'question_id': question['id'],
                    'has_scenario': question['has_scenario'],
                    'has_table': question['has_table'],
                    'has_image': question['has_image'],
                    'question_only': question['text'],
                }
            }
            chunks.append(chunk)

        # Also create chunks for standalone scenarios
        for scenario in structured_content['scenarios']:
            # Only add if not already included with a question
            if not any(scenario['text'] in chunk['text'] for chunk in chunks):
                chunk = {
                    'text': f"Context/Background:\n{scenario['text']}",
                    'metadata': {
                        'type': 'scenario',
                        'page': scenario['page'],
                    }
                }
                chunks.append(chunk)

        return chunks

    def _find_relevant_scenario(self, question: Dict, scenarios: List[Dict]) -> Optional[str]:
        """Find scenario relevant to a question."""
        if not question.get('has_scenario'):
            return None

        # Simple heuristic: find closest scenario before the question
        # In real implementation, could use more sophisticated matching
        if scenarios:
            # Return the last scenario (most likely to be relevant)
            return scenarios[-1]['text']

        return None

    def _find_relevant_table(self, question: Dict, structured_content: Dict) -> Optional[str]:
        """Find table relevant to a question."""
        if not question.get('has_table'):
            return None

        # Find tables in the document
        all_tables = []
        for page in structured_content['pages']:
            all_tables.extend(page['tables'])

        if not all_tables:
            return None

        # Return the last table (simple heuristic)
        table_data = all_tables[-1]['data']
        return self._format_table_as_text(table_data)

    def _format_table_as_text(self, table_data: List[List[str]]) -> str:
        """Format table data as readable text."""
        if not table_data:
            return ""

        # Create a simple text representation
        lines = []
        for row in table_data:
            lines.append(" | ".join(str(cell) if cell else "" for cell in row))

        return "\n".join(lines)
