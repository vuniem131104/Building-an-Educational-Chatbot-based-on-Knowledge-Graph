from indexing.shared.settings.chunker import ChunkerSetting
from indexing.shared.utils import tokens_calculator
from base import BaseModel 
from base import BaseService
from logger import get_logger

from indexing.domain.chunker.utils import get_parent_headers
from indexing.domain.chunker.utils import parse_headers
from indexing.domain.chunker.utils import split_chunks_by_tokens

logger = get_logger(__name__)


class ChunkerInput(BaseModel):
    contents: str
    file_name: str


class ChunkerOutput(BaseModel):
    chunks: list[str]
    file_name: str


class ChunkerService(BaseService):
    chunker_setting: ChunkerSetting

    def process(self, inputs: ChunkerInput) -> ChunkerOutput:
        """ Processes the input to split contents into chunks based on headers and token limits.

        Args:
            inputs (ChunkerInput): Input data containing contents, file name, positions, and unit.

        Returns:
            ChunkerOutput: Output data containing processed chunks, file name, positions, and unit.
        """
        
        try:
            chunks = self._split_chunks_by_headers(inputs.contents, inputs.file_name)

            return ChunkerOutput(
                chunks=chunks,
                file_name=inputs.file_name,
            )
        except Exception as e:
            logger.exception(
                'Error occurred while processing chunking',
                extra={
                    'file_name': inputs.file_name,
                    'error': str(e),
                }
            )


    def _split_chunks_by_headers(self, text: str, file_name: str) -> list[str]:
        """
        Splits the text into chunks based on headers and token limits.

        Args:
            text (str): The input text to be split into chunks.
            file_name (str): The name of the file being processed.

        Returns:
            list[str]: A list of chunks.
        """
        lines = text.strip().splitlines()
        headers = parse_headers(lines)
        chunks: list[list[str]] = []

        if len(headers) < 2:
            chunks = split_chunks_by_tokens(
                lines,
                [],
                0,
                self.chunker_setting.max_token_per_chunk,
                self.chunker_setting.min_token_per_chunk,
            )
            return ['\n'.join(chunk) for chunk in chunks if chunk]

        start_chunk: list[str]
        if headers[0][0] != 0:
            start_chunk = lines[: headers[0][0]]
        else:
            start_chunk = []
        content_lines: list[str] = []
        start_idx: int = headers[0][0] if headers else 0

        for header_index, (header_line_index, _, _) in enumerate(headers):
            end_line_index: int = (
                headers[header_index + 1][0] if header_index + 1 < len(headers) else len(lines)
            )
            new_content_lines: list[str] = lines[header_line_index:end_line_index]
            section_text: str = '\n'.join(content_lines + new_content_lines).strip()

            if tokens_calculator(section_text) <= self.chunker_setting.max_token_per_chunk:
                content_lines = content_lines + new_content_lines
            else:
                if content_lines:
                    content_lines = get_parent_headers(start_idx, headers) + content_lines
                    chunks.append(content_lines)
                if (
                    tokens_calculator('\n'.join(new_content_lines).strip())
                    > self.chunker_setting.max_token_per_chunk
                ):
                    chunks.extend(
                        split_chunks_by_tokens(
                            new_content_lines,
                            headers,
                            header_line_index,
                            self.chunker_setting.max_token_per_chunk,
                            self.chunker_setting.min_token_per_chunk,
                        ),
                    )
                    content_lines = []
                    start_idx = end_line_index
                else:
                    content_lines = new_content_lines
                    start_idx = header_line_index
        if content_lines:
            if (
                tokens_calculator('\n'.join(content_lines).strip())
                < self.chunker_setting.min_token_per_chunk
            ):
                if len(chunks) > 0:
                    chunks[-1].extend(content_lines)
                else:
                    chunks.append(content_lines)
            else:
                content_lines = get_parent_headers(start_idx, headers) + content_lines
                chunks.append(content_lines)

        # Handle start_chunk safely
        if (
            start_chunk
            and tokens_calculator('\n'.join(start_chunk).strip())
            < self.chunker_setting.min_token_per_chunk
        ):
            if chunks:  # Ensure chunks is not empty
                chunks[0] = start_chunk + chunks[0]
            else:
                chunks.append(start_chunk)
        elif start_chunk:  # Only process if start_chunk is not empty
            chunks.insert(0, start_chunk)

        # remove header if it is at the bottom of the chunk
        chunks = self._remove_bottom_header(chunks, file_name)
        return ['\n'.join(chunk) for chunk in chunks if chunk]
    

    def _remove_bottom_header(self, chunks: list[list[str]], file_name: str) -> list[list[str]]:
        """Removes the header from the bottom of each chunk if it is present.

        Args:
            chunks (list[list[str]]): The list of chunks to process.
            file_name (str): The name of the file to be added at the top of each chunk.

        Returns:
            list[list[str]]: The processed list of chunks with headers removed from the bottom.
        """
        file_name_text: str = f'**{file_name}**\n'
        for chunk_index, chunk in enumerate(chunks):
            if not chunk:
                continue
            end_index: int = len(chunk)
            for line_index in range(-1, -len(chunk) - 1, -1):
                if chunk[line_index].strip().startswith('#') or chunk[line_index].strip() == '':
                    end_index = line_index
                    continue
                else:
                    break
            chunks[chunk_index] = chunks[chunk_index][:end_index]
            # add file name at the top of the chunk
            if chunks[chunk_index]:  # More pythonic than != []
                chunks[chunk_index].insert(0, file_name_text)
        return chunks


if __name__ == "__main__":
    # Example usage
    service = ChunkerService(chunker_setting=ChunkerSetting(
        max_token_per_chunk=1000,
        min_token_per_chunk=500,
    ))
    with open("/home/vuiem/KLTN/test/parser/Lecture2_General Concepts for ML_parser.txt", "r") as file:
        contents = file.read()
        input_data = ChunkerInput(contents=contents, file_name="Lecture2_General Concepts for ML.pdf")

    output_data = service.process(input_data)
    with open('chunks.txt', 'w') as f:
        for i, chunk in enumerate(output_data.chunks):
            f.write(f"Chunk {i + 1}:\n")
            f.write(chunk + '\n\n')