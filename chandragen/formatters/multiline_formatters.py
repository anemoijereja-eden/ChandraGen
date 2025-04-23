from chandragen.types import MultilineFormatter, JobConfig as Config, FormatterFlags as Flags
import textwrap

class FormatTablesAsUnicode(MultilineFormatter):
    name = "format_tables_as_unicode"
    description = """
    Format tables as unicode
    
    This multiline formatter takes a markdown table, parses it,
    and draws a fancy unicode box-drawing table with the data contained.
    Currently only supports 2-column tables, with the first row containing the labels.
    """
    valid_types = ["md", "mdx"]
    start_pattern = r"^\|.*\|"
    end_pattern = r"^(?!\|).*"
    
    def apply(self, buffer: list, config: Config, flags: Flags) -> list:
        print("running table formatter")
        table = [i[2:-2].split(" | ") for i in buffer]   # take the buffer and convert the table lines into a 2d list
        table_width: int = config.preformatted_unicode_columns
        clean_table = []
        column_width = max(len(column.strip()) for column in table[0])
        for x, y in enumerate(table):               # strips the seperating line 
            if not all( char == '-' for char in y[0]):      # Check if first column of row is all dashes. if it is, it's a seperator row and should be discarded.
                clean0 = y[0].strip() # Generate cleaned version of columns 0 and 1
                clean1 = y[1].strip()
                wrapped_text = textwrap.wrap(clean1, width = (table_width - column_width) - 5)
                clean_table.append([clean0, wrapped_text[0]])
                for segment in wrapped_text[1:]:
                    clean_table.append([" "*column_width, segment])
                clean_table.append(["",""]) # add a blank line between each row for readability
    
        final_table = [
            "```\n",
            f"┌{'─'*(column_width+2)}┬{'─'*((table_width - 3) - column_width)}┐\n",
            *[
                f"├{'─'*(column_width+2)}┼{'─'*((table_width - 3) - column_width)}┤\n" if idx == 1 else "" +
                f"│ {row[0] + ' '*(column_width - len(row[0]))} │ {row[1] + ' '*((table_width - 4) - (len(row[1]) + column_width))}│\n"
                for idx, row in enumerate(clean_table)
            ],
            f"└{'─'*(column_width+2)}┴{'─'*((table_width - 3) - column_width)}┘\n```\n"
        ]
        return final_table
