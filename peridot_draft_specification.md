# Draft Spec for Peridot
### Peridot is a templating and dynamic generation format for the Gemini protocol, similar in spirit to how Markdown formats content for the web.
This is an early version of the spec, and is going to change as tooling is developed for it.

## Core Principles:
- Peridot files are a **strict superset of Gemtext**, preserving 100% compatibility.
- Substitution syntax is **line-first and symbol-driven**, respecting Gemini's simplicity.
- Substitution elements allow **dynamic content** like indexes, counters, tables, etc., to be inserted at generation time.

## Substitution Syntax:
- **Inline Substitution:**  
  `<<substitution:(option: value, option2: value)>>`  
  For inserting small dynamic pieces, like numbers, phrases, or short text fragments.

- **Line Substitution:**  
  `>>> substitution: (option: value, option2: value)`  
  For inserting or replacing whole lines of generated content, such as a single-link, banner, etc.

- **Block Substitution:**  
  `>>{ substitution: (option:value)` ... `>>}`
  For inserting complex multi-line structures like tables or dynamically generated art.

> Note: All substitution options should be specified **right after** the starting line for multi-line blocks.

---

## Standard Substitution Handlers:
Peridot defines some **standard built-in handlers** that all compliant engines should support:

- `table` — Renders a dynamic table based on provided rows/columns/options.
- `counter` — Inserts or auto-increments a counter value.
- `slugify` — Converts a string to a URL/path-safe slug.
- `toc` — Inserts a Table of Contents based on headings in the document.
- `timestamp` — Inserts the current timestamp in a specified format.

Future versions of Peridot may define additional standard handlers.

---

## Extensibility:
- Substitution handlers are **modular** and **pipeline-based**, like formatters in ChandraGen.
- Peridot engines should allow **plugin loading** to add custom substitution behaviors.
- Aliasing and default options for handlers should be supported via configuration files.

---
