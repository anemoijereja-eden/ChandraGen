import textwrap

from chandragen.types import FormatterFlags as Flags
from chandragen.types import JobConfig as Config
from chandragen.types import MultilineFormatter


class FormatTablesAsUnicode(MultilineFormatter):
    def __init__(self):
        super().__init__(
            "format_tables_as_unicode",
            """
    Format tables as unicode
    
    This multiline formatter takes a markdown table, parses it,
    and draws a fancy unicode box-drawing table with the data contained.
    Currently only supports 2-column tables, with the first row containing the labels.
            """,
            ["md", "mdx"],
            r"^\|.*\|",
            r"^(?!\|).*"
        )

    @classmethod
    def create(cls) -> MultilineFormatter:
        return cls()
        
    def apply(self, buffer: list[str], config: Config, flags: Flags) -> list[str]:
        table = [i[2:-2].split(" | ") for i in buffer]   # take the buffer and convert the table lines into a 2d list
        table_width: int = config.preformatted_unicode_columns
        clean_table: list[list[str]] = []
        column_width = max(len(column.strip()) for column in table[0])
        for row in table:               # strips the seperating line 
            if not all( char == "-" for char in row[0]):      # Check if first column of row is all dashes. if it is, it's a seperator row and should be discarded.
                clean0 = row[0].strip() # Generate cleaned version of columns 0 and 1
                clean1 = row[1].strip()
                wrapped_text = textwrap.wrap(clean1, width = (table_width - column_width) - 5)
                clean_table.append([clean0, wrapped_text[0]])
                clean_table += [[" " * column_width, segment] for segment in wrapped_text[1:]]
                clean_table.append(["",""]) # add a blank line between each row for readability
    
        return [
            "```\n",
            f"┌{'─'*(column_width+2)}┬{'─'*((table_width - 3) - column_width)}┐\n",
            *[
                f"├{'─'*(column_width+2)}┼{'─'*((table_width - 3) - column_width)}┤\n" if idx == 1 else "" +
                f"│ {row[0] + ' '*(column_width - len(row[0]))} │ {row[1] + ' '*((table_width - 4) - (len(row[1]) + column_width))}│\n"
                for idx, row in enumerate(clean_table)
            ],
            f"└{'─'*(column_width+2)}┴{'─'*((table_width - 3) - column_width)}┘\n```\n"
        ]
