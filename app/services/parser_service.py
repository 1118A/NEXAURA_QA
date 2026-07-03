import hashlib
import logging
from typing import List, Set, Dict, Any, Tuple
from pathlib import Path

from app.models.schemas import CodeFile, CodeChunk
from app.exceptions import ParserError

# Import tree-sitter bindings
import tree_sitter_python
import tree_sitter_javascript
import tree_sitter_typescript
from tree_sitter import Language, Parser

logger = logging.getLogger(__name__)

# Symbol types to search for in tree-sitter AST
PYTHON_SYMBOLS = {
    "class_definition": "class",
    "function_definition": "function",
}

JS_TS_SYMBOLS = {
    "class_declaration": "class",
    "class": "class",
    "function_declaration": "function",
    "method_definition": "method",
    "arrow_function": "function",
}

class ParserService:
    @staticmethod
    def detect_language(extension: str) -> str:
        ext = extension.lower()
        if ext == ".py":
            return "python"
        elif ext in [".js", ".jsx"]:
            return "javascript"
        elif ext in [".ts", ".tsx"]:
            return "typescript"
        return "unknown"

    def get_parser_for_extension(self, extension: str) -> Tuple[Parser, str]:
        """Load parser and identify the language type."""
        ext = extension.lower()
        try:
            if ext == ".py":
                lang = Language(tree_sitter_python.language())
                return Parser(lang), "python"
            elif ext in [".js", ".jsx"]:
                lang = Language(tree_sitter_javascript.language())
                return Parser(lang), "javascript"
            elif ext == ".ts":
                lang = Language(tree_sitter_typescript.language_typescript())
                return Parser(lang), "typescript"
            elif ext == ".tsx":
                # Use TSX language definition
                try:
                    lang = Language(tree_sitter_typescript.language_tsx())
                except Exception:
                    lang = Language(tree_sitter_typescript.language_typescript())
                return Parser(lang), "typescript"
        except Exception as e:
            logger.error(f"Failed to initialize tree-sitter parser for {extension}: {str(e)}")
            raise ParserError(f"Tree-sitter parser initialization failed: {str(e)}")
            
        raise ParserError(f"Unsupported extension: {extension}")

    def make_chunk_id(self, relative_path: str, start_line: int, end_line: int, content: str) -> str:
        raw = f"{relative_path}:{start_line}:{end_line}:{content}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def get_node_text(self, content: str, start_byte: int, end_byte: int) -> str:
        return content.encode("utf-8")[start_byte:end_byte].decode("utf-8", errors="ignore")

    def get_symbol_name(self, node, content: str) -> str:
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            return self.get_node_text(content, name_node.start_byte, name_node.end_byte)
            
        if node.type == "arrow_function" and node.parent is not None:
            parent = node.parent
            if parent.type == "variable_declarator":
                id_node = parent.child_by_field_name("id")
                if id_node is not None:
                    return self.get_node_text(content, id_node.start_byte, id_node.end_byte)
        return "anonymous"

    def fallback_line_chunks(self, code_file: CodeFile, max_chunk_chars: int) -> List[CodeChunk]:
        """Simple line-based chunking as a safety fallback."""
        logger.info(f"Using fallback line chunking for: {code_file.relative_path}")
        lines = code_file.content.splitlines()
        chunks = []
        language = self.detect_language(code_file.extension)
        
        current_lines = []
        current_len = 0
        start_line = 1
        
        for idx, line in enumerate(lines):
            line_len = len(line) + 1
            if current_len + line_len > max_chunk_chars and current_lines:
                chunk_content = "\n".join(current_lines)
                end_line = idx
                chunk_id = self.make_chunk_id(code_file.relative_path, start_line, end_line, chunk_content)
                chunks.append(
                    CodeChunk(
                        chunk_id=chunk_id,
                        file_path=code_file.file_path,
                        relative_path=code_file.relative_path,
                        content=chunk_content,
                        start_line=start_line,
                        end_line=end_line,
                        symbol_name=None,
                        symbol_type="block",
                        language=language
                    )
                )
                start_line = idx + 1
                current_lines = []
                current_len = 0
                
            current_lines.append(line)
            current_len += line_len
            
        if current_lines:
            chunk_content = "\n".join(current_lines)
            end_line = len(lines)
            chunk_id = self.make_chunk_id(code_file.relative_path, start_line, end_line, chunk_content)
            chunks.append(
                CodeChunk(
                    chunk_id=chunk_id,
                    file_path=code_file.file_path,
                    relative_path=code_file.relative_path,
                    content=chunk_content,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_name=None,
                    symbol_type="block",
                    language=language
                )
            )
            
        return chunks

    def split_lines_to_sub_chunks(self, lines: List[str], start_line_num: int, max_chars: int) -> List[Tuple[str, int, int]]:
        """Splits list of code lines into character-bounded blocks without breaking lines."""
        sub_chunks = []
        current_lines = []
        current_len = 0
        current_start = start_line_num
        
        for i, line in enumerate(lines):
            line_len = len(line) + 1  # count newline
            
            if current_len + line_len > max_chars and current_lines:
                sub_content = "\n".join(current_lines)
                sub_chunks.append((sub_content, current_start, current_start + len(current_lines) - 1))
                current_start = current_start + len(current_lines)
                current_lines = []
                current_len = 0
                
            current_lines.append(line)
            current_len += line_len
            
        if current_lines:
            sub_content = "\n".join(current_lines)
            sub_chunks.append((sub_content, current_start, current_start + len(current_lines) - 1))
            
        return sub_chunks

    def parse_code_file(self, code_file: CodeFile, max_chunk_chars: int = 2500) -> List[CodeChunk]:
        language = self.detect_language(code_file.extension)
        if language == "unknown":
            return self.fallback_line_chunks(code_file, max_chunk_chars)

        try:
            parser, lang_name = self.get_parser_for_extension(code_file.extension)
            tree = parser.parse(code_file.content.encode("utf-8"))
        except Exception as e:
            logger.warning(f"Tree-sitter parse failed for {code_file.relative_path}: {str(e)}. Falling back...")
            return self.fallback_line_chunks(code_file, max_chunk_chars)

        chunks = []
        file_lines = code_file.content.splitlines()
        total_lines_count = len(file_lines)
        
        # Track covered line numbers (1-indexed)
        covered_lines: Set[int] = set()
        
        symbols_dict = PYTHON_SYMBOLS if lang_name == "python" else JS_TS_SYMBOLS
        root = tree.root_node
        
        # Traverse AST and gather symbols of interest
        symbol_nodes = []
        
        def walk(node):
            if node.type in symbols_dict:
                symbol_type = symbols_dict[node.type]
                symbol_name = self.get_symbol_name(node, code_file.content)
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                
                # Limit bounds to actual file size
                start_line = max(1, min(start_line, total_lines_count))
                end_line = max(start_line, min(end_line, total_lines_count))
                
                symbol_nodes.append({
                    "symbol_type": symbol_type,
                    "symbol_name": symbol_name,
                    "start_line": start_line,
                    "end_line": end_line,
                })
                
                # Mark these lines as covered by AST symbol definition
                for line_idx in range(start_line, end_line + 1):
                    covered_lines.add(line_idx)
                    
            for child in node.children:
                walk(child)
                
        walk(root)

        # Generate chunks for AST symbols
        for symbol in symbol_nodes:
            s_line = symbol["start_line"]
            e_line = symbol["end_line"]
            
            # Slice lines corresponding to the symbol node
            symbol_lines = file_lines[s_line - 1 : e_line]
            symbol_content = "\n".join(symbol_lines)
            
            if not symbol_content.strip():
                continue
                
            # If the block is within size limit, load it
            if len(symbol_content) <= max_chunk_chars:
                chunk_id = self.make_chunk_id(code_file.relative_path, s_line, e_line, symbol_content)
                chunks.append(
                    CodeChunk(
                        chunk_id=chunk_id,
                        file_path=code_file.file_path,
                        relative_path=code_file.relative_path,
                        content=symbol_content,
                        start_line=s_line,
                        end_line=e_line,
                        symbol_name=symbol["symbol_name"],
                        symbol_type=symbol["symbol_type"],
                        language=lang_name
                    )
                )
            else:
                # Split large symbol into character-bounded chunks
                sub_blocks = self.split_lines_to_sub_chunks(symbol_lines, s_line, max_chunk_chars)
                for sub_content, sub_s, sub_e in sub_blocks:
                    if not sub_content.strip():
                        continue
                    chunk_id = self.make_chunk_id(code_file.relative_path, sub_s, sub_e, sub_content)
                    chunks.append(
                        CodeChunk(
                            chunk_id=chunk_id,
                            file_path=code_file.file_path,
                            relative_path=code_file.relative_path,
                            content=sub_content,
                            start_line=sub_s,
                            end_line=sub_e,
                            symbol_name=symbol["symbol_name"] + " (split)",
                            symbol_type=symbol["symbol_type"],
                            language=lang_name
                        )
                    )

        # Identify contiguous uncovered line ranges
        uncovered_ranges: List[Tuple[int, int]] = []
        current_range_start = None
        
        for line_num in range(1, total_lines_count + 1):
            if line_num not in covered_lines:
                if current_range_start is None:
                    current_range_start = line_num
            else:
                if current_range_start is not None:
                    uncovered_ranges.append((current_range_start, line_num - 1))
                    current_range_start = None
                    
        if current_range_start is not None:
            uncovered_ranges.append((current_range_start, total_lines_count))

        # Create block chunks from the uncovered ranges
        for start, end in uncovered_ranges:
            range_lines = file_lines[start - 1 : end]
            range_content = "\n".join(range_lines)
            if not range_content.strip():
                continue
                
            if len(range_content) <= max_chunk_chars:
                chunk_id = self.make_chunk_id(code_file.relative_path, start, end, range_content)
                chunks.append(
                    CodeChunk(
                        chunk_id=chunk_id,
                        file_path=code_file.file_path,
                        relative_path=code_file.relative_path,
                        content=range_content,
                        start_line=start,
                        end_line=end,
                        symbol_name=None,
                        symbol_type="block",
                        language=lang_name
                    )
                )
            else:
                sub_blocks = self.split_lines_to_sub_chunks(range_lines, start, max_chunk_chars)
                for sub_content, sub_s, sub_e in sub_blocks:
                    if not sub_content.strip():
                        continue
                    chunk_id = self.make_chunk_id(code_file.relative_path, sub_s, sub_e, sub_content)
                    chunks.append(
                        CodeChunk(
                            chunk_id=chunk_id,
                            file_path=code_file.file_path,
                            relative_path=code_file.relative_path,
                            content=sub_content,
                            start_line=sub_s,
                            end_line=sub_e,
                            symbol_name=None,
                            symbol_type="block",
                            language=lang_name
                        )
                    )

        # Safety fallback if parser service processed symbols but generated empty chunks
        if not chunks:
            return self.fallback_line_chunks(code_file, max_chunk_chars)

        return chunks

    def parse_code_files(self, code_files: List[CodeFile], max_chunk_chars: int = 2500) -> List[CodeChunk]:
        all_chunks = []
        for code_file in code_files:
            file_chunks = self.parse_code_file(code_file, max_chunk_chars)
            all_chunks.extend(file_chunks)
        return all_chunks
