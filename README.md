# ChandraGen
Built for quiet web enthusiasts, ChandraGen connects existing MDX-based frameworks to geminispace.
ChandraGen allows users to see a new layer of your site, similarly to how the Chandra X-Ray observatory it's named after revealed a new visual layer of the cosmos.

ChandraGen started as a simple converter script that built a gemini page dynamically from the markdown document used to house the https://allthingslinux.org code of conduct. as the scope of thegemini capsule project I head for that organization grew, it became clear that a framework like this would be necessary, but I found no options for it that fit our usecase. as such, I've taken the project on myself. I hope you're able to find ChandraGen useful!

## Poetry
ChandraGen now uses Poetry to manage dependencies and provide an easy way to run the ChandraGen CLI

## Configurability
ChandraGen currently supports running a config file using the `poetry run chandragen run-config <path>` command.
Use the example config to see what keys it supports. ChandraGen supports setting as many targets as you want, both as dirs anf files. the recursive flag can be set on a dir entry to have it recursively grab every formattable file it can find. the config must have a default config defined, which can then have sections overridden under the config for each target.

## Extensibility
ChandraGen supports external formatters via a plugin system. you can find an example plugin in the plugins directory. plugin formatters can be called the same way as internal formatters in the configuration. you can use `poetry run chandragen list-formatters` to get the currently available internal and external formatters. built-in formatter documentation is in the works.

## The codebase
ChandraGen is build entirely using python simply because that's the best language I know for string manipulation. the formatting system is simple enough that it still runs pretty fast without excessive overhead despite being in python. 

# TODO:
- Write the config parser and logic for batching and formatting files as defined by a configuration
- formatter class metadata (built-in documentation, priority system)
- extend formatter class system to also support multi-line formatters and document pre-processors
- allow formatter classes to specify a MIME type and extend file extension support at the batching steps
- Add additional formatters to handle inline markdown links
- Find a way to add conversion hints and gemini-only tags to an mdx document, and implement parsing for them
- Write a Dockerfile for this, make it integrate cleanly in a docker compose that builds ChandraGen and a gemini server line Gemserv
- Integration with common MDX-based http ssg frameworks
- Contributor documentation
- CI, Linting, Strict type checking, and dependency management
